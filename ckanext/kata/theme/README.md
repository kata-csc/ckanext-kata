# Compiling styles

Styles are in Less format. The `lessc` compiler is expected to be found under `node_modules` of the sibling `ckan` project (less v1.7.5 should already be installed there).

Install requirements to the same location as less (`sources/ckan`):
```
npm install nodewatch autoprefixer-cli
```
Note: From less 2.x onwards there's an autoprefixer plugin for less. For less 1.x we need to use the standalone solution.

**Don't edit the file `public/css/kata.css` manually.**

**If you change the styles, remember to compile the `kata.css` file before committing.**

1. Edit the `.less` files under `public/less`. If you need new modules, create a new file and `@import` it in `main.less`
2. Compile the styles into `kata.css` with the script `./less`. This also starts _nodewatch_ so you can continue to edit the styles and compilation is done on save.
