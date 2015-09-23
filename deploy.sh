rm -rf deploy
mkdir deploy

export IMAGE_BASE_URL=http://dev.assets.neo4j.com.s3.amazonaws.com/wp-content/uploads/
export GITHUB=https://github.com/neo4j-contrib/developer-resources/tree/gh-pages
export MANUAL=http://neo4j.com/docs/stable
export EXAMPLES=https://github.com/neo4j-examples

for file in `find . -mindepth 2 -maxdepth 3 -name "*.adoc"`; do
   echo "Rendering $file"
   filename=${file##*/}
   filename=${filename%.adoc}
   bundle exec asciidoctor -a allow-uri-read -a source-highlighter=codemirror -a linkattrs -a img=${IMAGE_BASE_URL} -a examples=${EXAMPLES} -a manual="${MANUAL}" -a github="${GITHUB}" -T _templates/wordpress $file -o deploy/${filename}.html 2>&1 | grep -v "out of sequence"
done

for guide in deploy/* ; do
  #./publish.rb $guide
done


#git add .
#git commit -m "content-update for github-pages"
#git push origin gh-pages
