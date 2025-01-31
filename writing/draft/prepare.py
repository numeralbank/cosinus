from sys import argv

with open(argv[1]) as f:
    content = f.read()

refs = []
for word in content.replace("\n", " ").split(" "):
    if word.startswith(":fig:"):
        word = ':' + word[1:].strip(".,;:")
        if word in refs:
            pass
        else:
            refs += [word]
js = """<script>
var i, fig;
var refs = {"""
for i, word in enumerate(refs):
    content = content.replace("#" + word, "#fig-" + str(i + 1))
    content = content.replace(word, str(i + 1))
    js += '"fig-{0}": {0}, '.format(i + 1)
js = js[:-2] + "};\n"
js += """for (i = 0; i < Object.keys(refs).length; i += 1) {
  fig = document.getElementById("fig-" + (i + 1)).children[1];
  fig.innerHTML = "Figure " + String(i + 1) + ": " + fig.innerHTML;
}
</script>
"""
    
with open("tmp.md", "w") as f:
    f.write(content)
    f.write(js)


