local opts = { noremap = true, silent = true }
local term_opts = { silent = true }

local km = vim.api.nvim_set_keymap


-- Modes
-- 	normal = "n"
-- 	insert = "i"
-- 	visual = "v"
-- 	visual_block_mode = "x"
-- 	term = "t"
-- 	command_mode = "c"
--
-- What do things mean?
-- 	C = cntrl
-- 	S = shift
-- 	CR = cariadge return (enter)
-- 	a = alt

-- visual mode
km("v", ",", "<gv", opts)
km("v", ".", ">gv", opts)


-- nvim-tree
km("n", "ge", ":NvimTreeToggle<cr>", opts)

-- Telescope
km("n", "<C-f>", "<cmd>Telescope live_grep<cr>", opts)
km("n", "<S-e>", "<cmd>lua require'telescope.builtin'.find_files(require('telescope.themes').get_dropdown({ previewer = false }))<cr>", opts)
