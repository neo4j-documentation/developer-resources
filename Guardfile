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
  watch(/.*\.(?:adoc|asciidoc)/) do |files|
    files.each do |file|
      puts
      run_script = File.join(Dir.pwd, 'render.rb')
      output = `#{run_script} #{file} 2>&1`
      puts output.split(/[\n\r]+/).reject {|line| line =~ /out of sequence/ }.join("\n")
    end
  end
end
