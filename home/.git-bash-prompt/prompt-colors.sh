#!/usr/bin/env bash
# prompt-colors.sh
#
# source this file to get color definitions
# are also printed to STDERR.

define_color_names() {

  ColorNames=( Black Red Green Yellow Blue Magenta Cyan White )
  FgColors=(    30   31   32    33     34   35      36   37  )
  BgColors=(    40   41   42    43     44   45      46   47  )

  local AttrNorm=0
  local AttrBright=1
  local AttrDim=2
  local AttrUnder=4
  local AttrBlink=5
  local AttrRev=7
  local AttrHide=8

  # define "BoldCOLOR", "BrightCOLOR", and "DimCOLOR" names

  # _map_colors ATTRNAME ATTRVALUE
  #
  # Defines three names for every color, attribute combintaion:
  #    {ATTRNAME}{COLORNAME}
  #    {ATTRNAME}{COLORNAME}Fg
  #    {ATTRNAME}{COLORNAME}Bg
  #
  # Example: BoldRed, BoldRedFg, BoldRedBg

  _map_colors() {
    local x=0
    local attrname="${1}"
    local attrcode="${2}"
    while (( x < 8 )) ; do
      local colorname="${ColorNames[x]}"
      local fgcolorcode="${FgColors[x]}"
      local bgcolorcode="${BgColors[x]}"
      longcolorname="${attrname}${colorname}"
      _def_color "${longcolorname}"   "${attrcode}" "${fgcolorcode}"
      _def_color "${longcolorname}Fg" "${attrcode}" "${fgcolorcode}"
      _def_color "${longcolorname}Bg" "${attrcode}" "${bgcolorcode}"
      (( x++ ))
    done
  }

  # _term_color [ N | N M | N M O... ]
  _term_color() {
    local cv
    cv="${1}"
    shift
    while [ -n "${1}" ]; do
      cv="${cv};${1}"
      shift
    done
    echo "\[\033[${cv}m\]"
  }

  # def_color NAME ATTRCODE COLORCODE
  _def_color() {
    local def="${1}=\"\`_term_color ${2} ${3}\`\""
    eval "${def}"
  }

  _def_256_color() {
    local def="${1}=\"\`_term_color ${2} 5 ${3}\`\""
    eval "${def}"
  }

  _map_colors Bold   ${AttrBright}
  _map_colors Bright ${AttrBright}
  _map_colors Dim    ${AttrDim}
  _map_colors ''     ${AttrNorm}

  _def_color IntenseBlack 0 90
  _def_color ResetColor   0 0

  _def_256_color BoldOrange 38 202
  _def_256_color BrightOrange 38 208
  _def_256_color DimOrange 38 130
  _def_256_color Orange 38 166

  _def_256_color BoldOrangeBg 48 202
  _def_256_color BrightOrangeBg 48 208
  _def_256_color DimOrangeBg 48 130
  _def_256_color OrangeBg 48 166

}

# do the color definitions only once
if [[ -z "${ColorNames+x}" || "${#ColorNames[*]}" = 0 || -z "${IntenseBlack:+x}" || -z "${ResetColor:+x}" ]]; then
  define_color_names
fi
