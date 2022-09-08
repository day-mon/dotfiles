local status_ok, _ = pcall(require, "lspconfig")
if not status_ok then
    vim.notify("lsp config is not okay")
    return
end

require("damon.lsp.lsp-installer")
require("damon.lsp.handlers").setup()

