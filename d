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

#remove all bash_completion, regenerate them
__d_generate_bash_completion()
{
    echo "$(basename "$0") $XARGPARES_VERSION"
    while read line; do
        rm -fr "$XARGPARES_COMPLETE_DIR/$line"
        if [[ "$line" != "d" ]]; then
            "$line"  >/dev/null 2>&1
        fi
    done < <( ls -1 "$XARGPARES_COMPLETE_DIR" )
}


__d_init

# call ourself
if [[ ! "$0" =~ ^-.* && "$(basename "$0")" == "$(basename "$BASH_SOURCE")" ]]; then 
    __d_generate_bash_completion
    exit 0
fi