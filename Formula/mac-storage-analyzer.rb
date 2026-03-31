class MacStorageAnalyzer < Formula
  desc "Analyze where your macOS System Data storage is going"
  homepage "https://github.com/mp9sit/mac_system_data_storage_analyzer"
  url "https://github.com/mp9sit/mac_system_data_storage_analyzer/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "a9e063213b804fb9c0a0ede44963def58337a9ab8b338685795d0871ca0641f3"
  license "MIT"

  def install
    bin.install "mac_storage_analyzer.py" => "mac-storage-analyzer"
    pkgshare.install "vendor_map.json"

    # Patch the script to find vendor_map.json in its installed location
    inreplace bin/"mac-storage-analyzer",
      'os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor_map.json")',
      "\"#{pkgshare}/vendor_map.json\""
  end

  test do
    # Verify script runs and shows help without error
    output = shell_output("#{bin}/mac-storage-analyzer --help")
    assert_match "scan-files", output
  end
end
