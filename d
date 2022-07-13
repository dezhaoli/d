#!/usr/bin/env -S bash
###########################################################
# @Author: dezhaoli@tencent.com
# @Date:   
# Please contact dezhaoli if you have any questions.
###########################################################
[[ -n "$XARGPARES_VERSION" ]] || . "$(which xargparse)"
[[ -n "$XFORMAT_VERSION" ]] || . "$(which xformat)"
[[ -n "$XWSL_EX_VERSION" ]] || . "$(which xwsl-ex)"


export LC_CTYPE=en_US.UTF-8

XFORMAT_IS_PRINT_TIME=true
XARGPARES_SMART_MODE=true

_d_add_path()
{
	local p="$1"
	if [[ ! "$PATH" =~ "$p" ]]; then
	  export PATH="$p:$PATH"
	fi
}


D_CONFIGURATION_FILE=~/.d/configuration.db


_d_pair_set()
{
	xpair set -f "$D_CONFIGURATION_FILE" "$1" "$2"
}
_d_pair_get()
{
	local value="$(xpair get -f "$D_CONFIGURATION_FILE" "$1")"
	printf -v "$2" "%s" "${value}"
}