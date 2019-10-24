source ~/.git-bash-prompt/prompt-colors.sh


if [[ -z "${ColorNames+x}" || "${#ColorNames[*]}" = 0 || -z "${IntenseBlack:+x}" || -z "${ResetColor:+x}" ]]; then
  define_color_names
fi

function showColor ()
{
  local color=$(eval echo "\${${1}}");
  local code=$(echo "${!1}" | sed 's/\\\[\\033\[//' | sed 's/m\\\]//')
  echo -e "  ${color}${1}${ResetColor}\t${code}" | sed 's/\\\]//g' | sed 's/\\\[//g'
}

showColor BrightOrange
showColor BoldOrange
showColor Orange
showColor DimOrange

