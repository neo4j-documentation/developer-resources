export GITHUB=https://github.com/neo4j-contrib/developer-resources/tree/gh-pages
export MANUAL=http://neo4j.com/docs/stable

function render {
   file="$1"
   to=${file%/*}/index.html
   echo "Rendering $file to $to"
   asciidoctor -a source-highlighter=codemirror -a linkattrs -a img=./ -a manual="${MANUAL}" -a github="${GITHUB}" -T _templates $file -o $to 2>&1 | grep -v "out of sequence"
}

if [ "$1" != "" ]; then
   render "$1"	
else
   for file in `find . -mindepth 2 -maxdepth 3 -name "*.adoc"`; do
    	render "$file"
   done
fi

#git add .
#git commit -m "content-update for github-pages"
#git push origin gh-pages
