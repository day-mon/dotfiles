local nmap = require("damon.utils").nmap
local nnoremap = require("damon.utils").nnoremap
local inoremap = require("damon.utils").inoremap
local vnoremap = require("damon.utils").vnoremap
local xnoremap = require("damon.utils").xnoremap

vim.g.mapleader = ' '

-- Normal mode
nnoremap("<C-h>", "<C-w>h")
nnoremap("<C-j>", "<C-w>j")
nnoremap("<C-k>", "<C-w>k")
nnoremap("<C-l>", "<C-w>l")

-- Insert mode
inoremap("jk", "<Esc>")
