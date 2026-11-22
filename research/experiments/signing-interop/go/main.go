// Bounded research driver. Fixed seeds are public, synthetic, TEST ONLY.
package main

import (
	"context"
	"crypto"
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"os"

	"github.com/secure-systems-lab/go-securesystemslib/dsse"
)

type key struct {
	public  ed25519.PublicKey
	private ed25519.PrivateKey
}

func (k key) Sign(_ context.Context, b []byte) ([]byte, error) {
	return ed25519.Sign(k.private, b), nil
}
func (k key) Verify(_ context.Context, b, s []byte) error {
	if !ed25519.Verify(k.public, b, s) {
		return errors.New("invalid signature")
	}
	return nil
}
func (k key) KeyID() (string, error)   { return "synthetic-test-only", nil }
func (k key) Public() crypto.PublicKey { return k.public }
func read(path string, limit int64) ([]byte, error) {
	f, e := os.Open(path)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	info, e := f.Stat()
	if e != nil {
		return nil, e
	}
	if info.Size() > limit {
		return nil, errors.New("input limit")
	}
	return os.ReadFile(path)
}
func run() error {
	if len(os.Args) < 2 {
		return errors.New("use public | sign payload | verify envelope public-key")
	}
	seed := make([]byte, 32)
	for i := range seed {
		seed[i] = 7
	}
	sk := ed25519.NewKeyFromSeed(seed)
	k := key{sk.Public().(ed25519.PublicKey), sk}
	switch os.Args[1] {
	case "commit":
		if len(os.Args) != 4 {
			return errors.New("commit requires catalogue and raw nonce files")
		}
		catalogue, e := read(os.Args[2], 1048576)
		if e != nil {
			return e
		}
		nonce, e := read(os.Args[3], 32)
		if e != nil {
			return e
		}
		digest, e := catalogueCommitment(catalogue, nonce)
		if e != nil {
			return e
		}
		_, e = fmt.Fprintln(os.Stdout, digest)
		return e
	case "public":
		_, e := os.Stdout.Write(k.public)
		return e
	case "sign":
		if len(os.Args) != 3 {
			return errors.New("sign requires payload")
		}
		b, e := read(os.Args[2], 8192)
		if e != nil {
			return e
		}
		signer, e := dsse.NewEnvelopeSigner(k)
		if e != nil {
			return e
		}
		env, e := signer.SignPayload(context.Background(), "application/vnd.in-toto+json", b)
		if e != nil {
			return e
		}
		return json.NewEncoder(os.Stdout).Encode(env)
	case "verify":
		if len(os.Args) != 4 {
			return errors.New("verify requires envelope and public key")
		}
		b, e := read(os.Args[2], 16384)
		if e != nil {
			return e
		}
		pub, e := read(os.Args[3], 32)
		if e != nil {
			return e
		}
		if len(pub) != 32 {
			return errors.New("public key length")
		}
		var env dsse.Envelope
		if e = json.Unmarshal(b, &env); e != nil {
			return e
		}
		if len(env.Signatures) != 1 {
			return errors.New("exactly one signature required")
		}
		v, e := dsse.NewEnvelopeVerifier(key{public: ed25519.PublicKey(pub)})
		if e != nil {
			return e
		}
		_, body, e := v.VerifyAndDecode(context.Background(), &env)
		if e != nil {
			return e
		}
		if len(body) > 8192 {
			return errors.New("payload limit")
		}
		_, e = os.Stdout.Write(body)
		return e
	}
	return errors.New("unknown operation")
}

// Exact-byte framing from spec/core.md. This function never parses catalogue JSON.
func catalogueCommitment(catalogue, nonce []byte) (string, error) {
	if len(nonce) != 32 {
		return "", errors.New("nonce must be exactly 32 bytes")
	}
	h := sha256.New()
	h.Write([]byte("Traceweave-Catalogue-v0.1\x00"))
	h.Write(nonce)
	var length [8]byte
	binary.BigEndian.PutUint64(length[:], uint64(len(catalogue)))
	h.Write(length[:])
	h.Write(catalogue)
	return fmt.Sprintf("%x", h.Sum(nil)), nil
}
func main() {
	if e := run(); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
