local status_okay, builtin = pcall(require, 'telescope.builtin')
if not status_okay then
	vim.notify('Oopsies telescope isnt working')
	vim.notify(builtin)
	return
end

vim.keymap.set('n', '<leader>pf', builtin.find_files, {})
vim.keymap.set('n', '<leader>ps', function() 
	builtin.grep_string({ search = vim.fn.input(" Grep > ") });
end)
