// Fixed seed is public, synthetic, TEST ONLY. This is a research driver.
use ed25519_compact::{KeyPair, Seed};
use sha2::{Digest, Sha256};
use std::{
    env, fs,
    io::{self, Write},
};
use wsc_dsse::{DsseEnvelope, Ed25519DsseSigner, Ed25519DsseVerifier};

fn read(path: &str, limit: u64) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    if fs::metadata(path)?.len() > limit {
        return Err("input limit".into());
    }
    Ok(fs::read(path)?)
}
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let pair = KeyPair::from_seed(Seed::new([9; 32]));
    let output = match args.get(1).map(String::as_str) {
        Some("commit") if args.len() == 4 => {
            let catalogue = read(&args[2], 1048576)?;
            let nonce = read(&args[3], 32)?;
            format!("{}\n", catalogue_commitment(&catalogue, &nonce)?).into_bytes()
        }
        Some("public") => pair.pk.to_vec(),
        Some("sign") if args.len() == 3 => {
            let payload = read(&args[2], 8192)?;
            let signer = Ed25519DsseSigner::new(pair.sk, Some("synthetic-test-only".into()));
            DsseEnvelope::sign(&payload, "application/vnd.in-toto+json", &signer)
                .map_err(|e| format!("{e:?}"))?
                .to_json()
                .map_err(|e| format!("{e:?}"))?
                .into_bytes()
        }
        Some("verify") if args.len() == 4 => {
            let input = read(&args[2], 16384)?;
            let public = read(&args[3], 32)?;
            let envelope = DsseEnvelope::from_json(std::str::from_utf8(&input)?)
                .map_err(|e| format!("{e:?}"))?;
            if envelope.signatures.len() != 1 {
                return Err("exactly one signature required".into());
            }
            let verifier =
                Ed25519DsseVerifier::from_bytes(&public).map_err(|e| format!("{e:?}"))?;
            let payload = envelope.verify(&verifier).map_err(|e| format!("{e:?}"))?;
            if payload.len() > 8192 {
                return Err("payload limit".into());
            }
            payload
        }
        _ => return Err("use public | sign payload | verify envelope public-key".into()),
    };
    io::stdout().write_all(&output)?;
    Ok(())
}

// Independent exact-byte framing from spec/core.md; catalogue bytes stay opaque.
fn catalogue_commitment(
    catalogue: &[u8],
    nonce: &[u8],
) -> Result<String, Box<dyn std::error::Error>> {
    if nonce.len() != 32 {
        return Err("nonce must be exactly 32 bytes".into());
    }
    let length = u64::try_from(catalogue.len())?;
    let mut hasher = Sha256::new();
    hasher.update(b"Traceweave-Catalogue-v0.1\0");
    hasher.update(nonce);
    hasher.update(length.to_be_bytes());
    hasher.update(catalogue);
    Ok(format!("{:x}", hasher.finalize()))
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
