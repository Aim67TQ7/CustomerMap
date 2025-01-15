
{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.glibcLocales
    pkgs.nodePackages.localtunnel
    pkgs.streamlit
  ];
}
