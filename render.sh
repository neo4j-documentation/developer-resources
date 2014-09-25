for file in `find . -mindepth 2 -name "*.adoc"`; do
   echo "Rendering $file"
   asciidoctor -a source-highlighter=codemirror -a img=./ -T _templates $file -o ${file%/*}/index.html
done

#git add .
#git commit -m "content-update for github-pages"
#git push origin gh-pages
