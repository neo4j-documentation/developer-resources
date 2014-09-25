rm -rf deploy
mkdir deploy

export IMAGE_BASE_URL=http://dev.assets.neo4j.com.s3.amazonaws.com/wp-content/uploads/

for file in `find . -mindepth 2 -name "*.adoc"`; do
   echo "Rendering $file"
   filename=${file##*/}
   filename=${filename%.adoc}
   bundle exec asciidoctor -a source-highlighter=codemirror -a img=${IMAGE_BASE_URL} -T _templates/wordpress $file -o deploy/${filename}.html
done
./publish.rb 'deploy/guide-build-a-recommendation-engine.html'

#git add .
#git commit -m "content-update for github-pages"
#git push origin gh-pages
