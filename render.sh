function render {
   file="$1"
   to=${file%/*}/index.html
   echo "Rendering $file to $to"
   asciidoctor -a source-highlighter=codemirror -a linkattrs -a img=./ -T _templates $file -o $to
}

if [ "$1" != "" ]; then
   render "$1"	
else
   for file in `find . -mindepth 2 -name "*.adoc"`; do
    	render "$file"
   done
fi

#git add .
#git commit -m "content-update for github-pages"
#git push origin gh-pages
