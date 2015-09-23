require 'guard/plugin'

module ::Guard
  class Slidy < ::Guard::Plugin
    def run_all
      true
    end

    def run_on_changes(paths)
      true
    end
  end
end


guard :slidy do
  watch(/.*\.(adoc|asciidoc)/) do |files|
    files.each do |file|
      puts "Compiling: asciidoc #{file}"

      run_script = File.join(Dir.pwd, 'render.sh')
      `#{run_script} #{file}`
    end
  end
end
