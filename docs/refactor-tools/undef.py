import ast,builtins,sys
for f in sys.argv[1:]:
    t=ast.parse(open(f).read());defined=set(dir(builtins))|{'__file__','__name__'}
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)):defined.add(n.name)
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            for a in n.names:defined.add((a.asname or a.name).split('.')[0])
        if isinstance(n,ast.Name) and isinstance(n.ctx,(ast.Store,ast.Del)):defined.add(n.id)
        if isinstance(n,ast.arg):defined.add(n.arg)
        if isinstance(n,ast.ExceptHandler) and n.name:defined.add(n.name)
    miss=sorted({n.id for n in ast.walk(t) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id not in defined})
    if miss:print(f,miss)
