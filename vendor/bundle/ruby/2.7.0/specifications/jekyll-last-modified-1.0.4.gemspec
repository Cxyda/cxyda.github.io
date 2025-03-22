# -*- encoding: utf-8 -*-
# stub: jekyll-last-modified 1.0.4 ruby lib

Gem::Specification.new do |s|
  s.name = "jekyll-last-modified".freeze
  s.version = "1.0.4"

  s.required_rubygems_version = Gem::Requirement.new(">= 0".freeze) if s.respond_to? :required_rubygems_version=
  s.require_paths = ["lib".freeze]
  s.authors = ["iBug".freeze]
  s.date = "2022-04-30"
  s.description = "Populate page date and last modified date from Git database".freeze
  s.email = ["i@ibugone.com".freeze]
  s.homepage = "https://github.com/iBug/jekyll-last-modified".freeze
  s.licenses = ["MIT".freeze]
  s.rubygems_version = "3.1.6".freeze
  s.summary = "Set page date from Git database".freeze

  s.installed_by_version = "3.1.6" if s.respond_to? :installed_by_version

  if s.respond_to? :specification_version then
    s.specification_version = 4
  end

  if s.respond_to? :add_runtime_dependency then
    s.add_runtime_dependency(%q<jekyll>.freeze, [">= 3.5"])
    s.add_development_dependency(%q<bundler>.freeze, [">= 1.6"])
    s.add_development_dependency(%q<shoulda>.freeze, [">= 0"])
    s.add_development_dependency(%q<mocha>.freeze, [">= 0"])
  else
    s.add_dependency(%q<jekyll>.freeze, [">= 3.5"])
    s.add_dependency(%q<bundler>.freeze, [">= 1.6"])
    s.add_dependency(%q<shoulda>.freeze, [">= 0"])
    s.add_dependency(%q<mocha>.freeze, [">= 0"])
  end
end
