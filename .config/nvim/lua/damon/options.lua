local options = {
    backup = false,
    shiftwidth = 4,
    cursorline = false,
    termguicolors = true,
    number = true,
    relativenumber = true,
    smartcase = true
}

for key, value in pairs(options) do
	vim.opt[key] = value
end
