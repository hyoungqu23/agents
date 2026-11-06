"""Generate a checksummed tap formula from the actual release artifacts."""
import argparse
import hashlib
from pathlib import Path
import re


def render(repository, tag, sdist, wheel, artifact_base=None):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Expected owner/repository')
    match = re.fullmatch(r'review-harness-v(\d+\.\d+\.\d+)', tag)
    if not match:
        raise ValueError('Expected a review-harness-vX.Y.Z release tag')
    version = match[1]
    if sdist.name != f'hm2_review_harness-{version}.tar.gz' or wheel.name != f'hm2_review_harness-{version}-py3-none-any.whl':
        raise ValueError('Artifact names must match the release version')
    base = artifact_base or f'https://github.com/{repository}/releases/download/{tag}'
    if not re.fullmatch(r'(?:https|file)://[^\s"\\]+', base):
        raise ValueError('Artifact base must be a literal HTTPS or file URL')
    return f'''class Hm2ReviewHarness < Formula
  include Language::Python::Virtualenv

  desc "Local draft-only automation for HM2 review workflows"
  homepage "https://github.com/{repository}"
  url "{base}/{sdist.name}"
  sha256 "{hashlib.sha256(sdist.read_bytes()).hexdigest()}"
  version "{version}"

  depends_on "python@3.14"
  depends_on "gh"
  depends_on "git"

  resource "harness-wheel" do
    url "{base}/{wheel.name}"
    sha256 "{hashlib.sha256(wheel.read_bytes()).hexdigest()}"
  end

  def install
    venv = virtualenv_create(libexec, "python3.14")
    venv.pip_install_and_link resource("harness-wheel")
  end

  service do
    run [opt_bin/"hm2-review-harness", "serve"]
    keep_alive true
    environment_variables PATH: std_service_path_env
    log_path var/"log/hm2-review-harness.log"
    error_log_path var/"log/hm2-review-harness-error.log"
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/hm2-review-harness --version")
    system bin/"hm2-review-harness", "--help"
  end
end
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True); parser.add_argument('--tag', required=True)
    parser.add_argument('--sdist', type=Path, required=True); parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifact-base', help='Local file URL for clean CI installation testing')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(args.repo, args.tag, args.sdist, args.wheel, args.artifact_base))


if __name__ == '__main__':
    main()
