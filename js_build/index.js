(function() {
  var SRC_BASE, action, compile, compress, concatenate, existsSync, expand, extname, fs, join, parser, resolve, uglify, _ref, _ref2;

  compile = require('coffee-script').compile;

  fs = require('fs');

  _ref = require('path'), join = _ref.join, existsSync = _ref.existsSync, extname = _ref.extname;

  _ref2 = require('uglify-js'), parser = _ref2.parser, uglify = _ref2.uglify;

  expand = function(dir) {
    return dir.replace(/^~/, process.env['HOME']);
  };

  SRC_BASE = expand(process.env['SRC_BASE'] || '~/src');

  resolve = function(paths) {
    return paths.map(function(p) {
      if (/^\/\//.test(p)) {
        return join(SRC_BASE, p.substring(2));
      } else {
        return p;
      }
    });
  };

  concatenate = function(paths, options) {
    var name, out, outf, path;
    name = options.name, out = options.out;
    if (!(name && out)) fail('Error: cannot concat files to nothing');
    path = join(out, "" + name + ".js");
    try {
      outf = fs.openSync(path, 'w+');
      paths.forEach(function(p) {
        var code;
        if (!existsSync(p)) fail("File not found: " + p);
        code = fs.readFileSync(p, 'utf8');
        if (extname(p === '.coffee')) code = compile(code);
        fs.writeSync(outf, code);
        return fs.writeSync(outf, '\n\n');
      });
    } finally {
      fs.closeSync(outf);
    }
    return path;
  };

  compress = function(path) {
    var ast, code, compressed, out;
    code = fs.readFileSync(path, 'utf8');
    ast = parser.parse(code);
    ast = uglify.ast_mangle(ast);
    ast = uglify.ast_squeeze(ast);
    compressed = uglify.gen_code(ast);
    out = path.replace(extname(path), ".min.js");
    fs.writeFileSync(out, compressed);
    return out;
  };

  action = function(defs) {
    var minify, out;
    out = defs.out, minify = defs.minify;
    return function(options) {
      var bundle, defaultTasks, files, minified, namespaceTasks;
      defaultTasks = jake.defaultNamespace.tasks;
      namespaceTasks = jake.currentNamespace.tasks;
      files = this.prereqs.filter(function(file) {
        if (file in defaultTasks || file in namespaceTasks) {
          return false;
        } else {
          return true;
        }
      });
      bundle = concatenate(files, {
        name: this.name,
        out: out
      });
      if (minify) minified = compress(bundle);
      return true;
    };
  };

  this.build = function(defs) {
    var deps, minify, name, out, srcs;
    name = defs.name, srcs = defs.srcs, deps = defs.deps, out = defs.out, minify = defs.minify;
    if (!(name || 'string' === typeof name)) {
      fail("Each build needs a name of type 'string', not " + name);
    }
    if (!(srcs || srcs.length)) fail('Each build needs at least one source file');
    deps || (deps = []);
    deps = resolve(deps.concat(srcs));
    out = join('./', out || 'build');
    if (!existsSync(out)) fs.mkdirSync(out);
    desc("Build task: " + name);
    return task(name, deps, action({
      out: out,
      minify: minify
    }));
  };

  desc('The default task');

  task('default', [], function() {});

}).call(this);
