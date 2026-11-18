// Synthetic feasibility checks only; not an embedder or a safety analyzer.
#[cfg(test)]
mod tests {
    use std::cell::RefCell;

    #[test]
    fn literal_bindings_retain_the_result_in_two_orders() {
        let original = {
            let a: i32 = 1;
            let b: i32 = 2;
            let c: i32 = 3;
            let d: i32 = 4;
            [a, b, c, d]
        };
        let reordered = {
            let d: i32 = 4;
            let b: i32 = 2;
            let a: i32 = 1;
            let c: i32 = 3;
            [a, b, c, d]
        };
        assert_eq!(original, reordered);
    }

    struct Guard<'a>(&'static str, &'a RefCell<Vec<&'static str>>);
    impl Drop for Guard<'_> {
        fn drop(&mut self) {
            self.1.borrow_mut().push(self.0);
        }
    }

    #[test]
    fn reordering_can_change_destructor_effects() {
        let original = RefCell::new(Vec::new());
        {
            let _a = Guard("a", &original);
            let _b = Guard("b", &original);
        }
        let reordered = RefCell::new(Vec::new());
        {
            let _b = Guard("b", &reordered);
            let _a = Guard("a", &reordered);
        }
        assert_eq!(*original.borrow(), vec!["b", "a"]);
        assert_eq!(*reordered.borrow(), vec!["a", "b"]);
    }
}
