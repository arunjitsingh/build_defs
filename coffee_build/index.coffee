# Build definitions for JavaScript/CoffeeScript.
# ---
# The module exports a `build` function that can be used to define a Jake task
# to concatenate, and optionally minify, JavaScript source files. CoffeeScript
# source files are compiled to JavaScript before concatenation/compression.
#
# Requires the `coffee-script` and `uglify-js` modules.
#
# Source files outside a project can be referenced by specifying the base path
# to the source tree in an environment variable (`SRC_BASE`), and referenced in
# the definitions by using `//` relative to the `SRC_BASE` (`SRC_BASE` defaults
# to `~/src`).
#
# Example Jakefile.coffee:
#     build
#       name: 'core'
#       srcs: ['core.js']
#       minify: yes
# That's it!

# Module requirements.
fs = require 'fs'
{join, existsSync, extname} = require 'path'
{compile} = require 'coffee-script'
{parser, uglify} = require 'uglify-js'


# Expands '~' to the user's home directory
expand = (dir) -> dir.replace /^~/, process.env['HOME']


# The base for sources. Source files outside a project directory can be accessed
# by prefixing `//` to the path relative to `SRC_BASE`.
SRC_BASE = expand process.env['SRC_BASE'] or '~/src'


# Resolves paths that start with `//` to `SRC_BASE`
# @param {!Array.<string>} paths The paths to resolve.
# @return {!Array.<string>} The resolved paths.
resolve = (paths) ->
  paths.map (p) -> if /^\/\//.test(p) then join SRC_BASE, p.substring(2) else p


# Concatenates the paths to a single file. CoffeeScript files are compiled to
# JavaScript first (based on their file extensions).
# @param {Object} options The name of the file and which directory the
#     concatenated file should be output to.
# @return {string} The path of the output file.
concatenate = (paths, options) ->
  # `name` and `out` are required.
  {name, out} = options
  fail 'Error: cannot concat files to nothing' unless name and out

  # The path for the output file.
  path = join out, "#{name}.js"

  try
    outf = fs.openSync path, 'w+'
    paths.forEach (p) ->
      # Read each input file that exists and write it to the open output file.
      fail "File not found: #{p}" unless existsSync p
      code = fs.readFileSync(p, 'utf8')
      # Compile CoffeeScript to JavaScript.
      code = compile code if extname p is '.coffee'
      fs.writeSync outf, code
      fs.writeSync outf, '\n\n'
  finally
    # Close the output file.
    fs.closeSync outf
  # Return the path of the output file.
  path


# Compresses a JavaScript file.
# @param {string} path The path of the input file.
# @return {string} The path of the output file.
compress = (path) ->
  code = fs.readFileSync(path, 'utf8')

  # Parse the code
  ast = parser.parse(code);

  # Get a new AST with mangled names
  ast = uglify.ast_mangle ast

  # AST with compression optimizations
  ast = uglify.ast_squeeze ast

  # Compressed code
  compressed = uglify.gen_code ast

  out = path.replace extname(path), ".min.js"
  fs.writeFileSync out, compressed
  out

# The task action to perform.
# @param {Object} defs The build definitions
# @return {function(this:jake.Task, Object)} The callback for the task.
action = (defs) ->
  {out, minify} = defs
  # The task callback.
  # @param {Object} options The parameters of the task.
  (options) ->
    # Filter out the task dependencies from the actual files. Anything that
    # isn't a task is assumed to be a file.
    defaultTasks = jake.defaultNamespace.tasks
    namespaceTasks = jake.currentNamespace.tasks
    files = @prereqs.filter (file) ->
      if (file of defaultTasks or file of namespaceTasks) then no else yes

    # Concatenate the files by default
    bundle = concatenate files, {@name, out}

    # If compression is required, minify the files.
    minified = compress bundle if minify

    # Done!
    yes


# The exported function that sets up the tasks and invokes the build process.
# @param {Object} defs The build definition.
@build = (defs) ->
  {name, srcs, deps, out, minify} = defs
  # `name` and `srcs` are required attributes.
  unless name or 'string' is typeof name
    fail "Each build needs a name of type 'string', not #{name}"
  unless srcs or srcs.length
    fail 'Each build needs at least one source file'
  deps or= []
  # The source files are also dependencies for Jake. Resolve `deps` and `srcs`.
  deps = resolve deps.concat(srcs)

  # Set the output directory. Create the directory if it doesn't exist.
  out = join './', out or 'build'
  fs.mkdirSync out unless existsSync out

  # The actual task.
  desc "Build task: #{name}"
  task name, deps, action {out, minify}


# Create a default task that doesn't do anything to keep Jake happy.
desc 'The default task'
task 'default', [], () ->

