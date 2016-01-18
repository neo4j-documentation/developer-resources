rm -rf deploy
mkdir deploy

export IMAGE_BASE_URL=http://dev.assets.neo4j.com.s3.amazonaws.com/wp-content/uploads/
export GITHUB=https://github.com/neo4j-contrib/developer-resources/tree/gh-pages
export MANUAL=http://neo4j.com/docs/stable
export EXAMPLES=https://github.com/neo4j-examples

i = 1
for file in `find . -mindepth 2 -maxdepth 4 -name "*.adoc"`; do
  echo "Rendering $file"
  filename=${file##*/}
  filename=${filename%.adoc}
  bundle exec asciidoctor \
    -a allow-uri-read,source-highlighter=codemirror,linkattrs,img=${IMAGE_BASE_URL},examples=${EXAMPLES},manual="${MANUAL}",github="${GITHUB}" \
    -T _templates/wordpress $file \
    -o deploy/${filename}.html 2>&1 \
      | grep -v "out of sequence" &

  ((i = i + 1))
  # Put the forking operator at the end of the asciidoctor line
  # This is here so that we only fork 4 at a time
  if ! ((i % 4)); then
    wait
  fi
done

./publish.rb deploy/*.html
