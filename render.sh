git checkout gh-pages

for file in *-*/*.adoc; do
   asciidoctor $file
done

git add *-*/*.html
git commit -m "content-update for github-pages"
git push origin gh-pages

git checkout master
