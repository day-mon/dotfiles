# Rust

Apply every relevant rule to Rust source.

- No comments at all, including `///` and `//!` doc comments.
- Helpers and constants go on the `impl` as associated functions and associated consts, not as free functions.
- Use reqwest's built-in retry policy and default headers instead of hand-rolled loops.
- Items stay private unless another crate needs them. Don't reach for `pub(crate)` by default.
- Turn on strict clippy lints in `Cargo.toml` `[lints]` and run `cargo clippy --all-targets -- -D warnings`.

```rust
impl NexusClient {
    const MAX_RETRIES: u32 = 3;

    fn page_url(&self, page: usize, per_page: usize) -> Url {
        let mut url = self.base.clone();
        url.query_pairs_mut()
            .append_pair("page", &page.to_string())
            .append_pair("per_page", &per_page.to_string());
        url
    }
}
```
