local status_okay, bultin = pcall(require, 'telescope.builtin')
if not status_okay then
	vim.notify('Oopsies telescope isnt working')
	vim.notify(bultin)
	return
end

vim.keymap.set('n', '<leader>pf', bultin.find_files, {})
vim.keymap.set('n', '<leader>ps', function() 
	builtin.grep_string({ search = vim.fn.input(" Grep > ") });
end)
