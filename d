#!/usr/bin/env -S bash
###########################################################
# @Author: dezhaoli@tencent.com
# @Date:   
# Please contact dezhaoli if you have any questions.
###########################################################

__d_init()
{
    [[ -n "$XARGPARES_VERSION" ]] || . "$(which xargparse)"
    [[ -n "$XFORMAT_VERSION" ]] || . "$(which xformat)"
    [[ -n "$XWSL_EX_VERSION" ]] || . "$(which xwsl-ex)"

    export LC_CTYPE=en_US.UTF-8

    XFORMAT_IS_PRINT_TIME=true
    XARGPARES_SMART_MODE=true

}




__d_add_path()
{
	local p="$1"
	if [[ ! "$PATH" =~ "$p" ]]; then
	  export PATH="$p:$PATH"
	fi
}

__d_nested_source()
{
    if [[ -n "${D_INHERIT_CLASS}" ]];then
        local tmp="$D_INHERIT_CLASS"
        unset D_INHERIT_CLASS D_IS_INHERIT
        source "$tmp"
    fi
}

# skip __d_init util D_INHERIT_CLASS is define

if ${D_IS_INHERIT:-false}; then
    __d_nested_source
else
    __d_init
fi



# when call ourself, remove all bash_completion, recreate it by calling the new script
if [[ ! "$0" =~ ^-.* && "$(basename "$0")" == "$(basename "$BASH_SOURCE")" ]]; then 
    echo "$(basename "$0") $XARGPARES_VERSION"
    dir=~/".xargparse/bash_completion.d"
    while read line; do
    	rm -fr "$dir/$line"
    	if [[ "$line" != "d" ]]; then
    		"$line"  >/dev/null 2>&1
    	fi
    done < <( ls -1 "$dir" )
    exit 0
fi