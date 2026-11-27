func save(w io.Writer) error {
	_, err := w.Write(buf)
	if err != nil {
		return err
	}
	buf = buf[:0]
	return nil
}
func load(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	cache = data
	return nil
}
