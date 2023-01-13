-- Learn the keybindings, see :help lsp-zero-keybindings
-- Learn to configure LSP servers, see :help lsp-zero-api-showcase
local okay, lsp = pcall(require, 'lsp-zero')

if not okay then
	vim.notify("Something went wrong with lsp")
	vim.notify(lsp)
end

vim.opt.signcolumn = 'yes'

lsp.preset('recommended')

lsp.ensure_installed({
  -- Replace these with whatever servers you want to install
  'tsserver',
  'eslint',
  'sumneko_lua',
})

-- Pass arguments to a language server
lsp.configure('tsserver', {
  on_attach = function(client, bufnr)
    print('hello tsserver')
  end,
  settings = {
    completions = {
      completeFunctionCalls = true
    }
  }
})

-- Configure lua language server for neovim
lsp.nvim_workspace()
lsp.setup()
