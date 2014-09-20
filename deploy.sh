rm -rf deploy
mkdir deploy

for file in `find . -mindepth 2 -name "*.adoc"`; do
   echo "Rendering $file"
   filename=${file##*/}
   filename=${filename%.adoc}
   bundle exec asciidoctor -a source-highlighter=codemirror -T _templates/wordpress $file -o deploy/${filename}.html
done
./publish.rb 'deploy/guide-build-a-recommendation-engine.html'

#git add .
#git commit -m "content-update for github-pages"
#git push origin gh-pages
