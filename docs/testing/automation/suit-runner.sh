#!/bin/sh
#
# Live test-suite runner. Catalogue is the suite markdown overview.
# Variants are shown under their parent and are not extra catalogue cases.
#
#   make test
#   make test SUITE=uv
#   sh docs/testing/automation/suit-runner.sh all|SUITE|CASE|VARIANT
#
# PK-001 is a reference to EV-001, not a second PASS.

automation_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$automation_dir/../../.." && pwd)
suites="EV PK RP PV FS CL DT OP NB RL RB UV"
pass_count=0
fail_count=0
manual_count=0
tbd_count=0
blocked_count=0
ref_count=0
displayed_count=0
catalogue_total=0
log_dir=$repo_root/tmp/suit-runner
status_col=64
sourced_suites=""

usage() {
	echo "usage: sh docs/testing/automation/suit-runner.sh CASE|SUITE|all" >&2
}

normalize_selector() {
	raw=$1
	lower=$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')
	if [ "$lower" = "all" ]; then
		printf '%s\n' "all"
	else
		printf '%s\n' "$raw" | tr '[:lower:]' '[:upper:]'
	fi
}

use_color() {
	if [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ]; then
		return 1
	fi
	return 0
}

print_colored_status() {
	color_status=$1
	if use_color; then
		case "$color_status" in
			PASS) printf '\033[32m%s\033[0m' "$color_status" ;;
			FAIL) printf '\033[31m%s\033[0m' "$color_status" ;;
			*) printf '\033[33m%s\033[0m' "$color_status" ;;
		esac
	else
		printf '%s' "$color_status"
	fi
}

flush_print() {
	awk -v s="$1" 'BEGIN { printf "%s", s; fflush(); }' 2>/dev/null || printf '%s' "$1"
}

suite_file() {
	printf '%s/%s.sh\n' "$automation_dir" "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
}

suite_markdown() {
	printf '%s/docs/testing/test_suites/%s.md\n' "$repo_root" "$1"
}

suite_heading() {
	heading_id=$1
	heading_md=$(suite_markdown "$heading_id")
	if [ -f "$heading_md" ]; then
		heading_text=$(awk '
			/^# [A-Z][A-Z] / {
				sub(/^# /, "")
				print
				exit
			}
		' "$heading_md")
		if [ -n "$heading_text" ]; then
			printf '%s\n' "$heading_text"
			return
		fi
	fi
	printf '%s\n' "$heading_id"
}

catalogue_rows() {
	cat_md=$(suite_markdown "$1")
	if [ ! -f "$cat_md" ]; then
		return 1
	fi
	awk -F '|' '
		{
			sid = $2
			gsub(/^[[:space:]]+|[[:space:]]+$/, "", sid)
			if (sid ~ /^[A-Z][A-Z]-[0-9][0-9][0-9]$/) {
				title = $3
				gsub(/^[[:space:]]+|[[:space:]]+$/, "", title)
				print sid "\t" title
			}
		}
	' "$cat_md"
}

catalogue_variants() {
	var_parent=$1
	var_suite=$2
	var_md=$(suite_markdown "$var_suite")
	if [ ! -f "$var_md" ]; then
		return
	fi
	awk -v parent="$var_parent" '
		$0 ~ "^### " parent "-[A-Z] " {
			line = $0
			sub(/^### /, "", line)
			vid = line
			sub(/ — .*/, "", vid)
			vname = line
			sub(/.* — /, "", vname)
			print vid "\t" vname
		}
	' "$var_md"
}

id_to_fn() {
	printf '%s\n' "$1" | tr '[:upper:]' '[:lower:]' | tr '-' '_'
}

source_suite() {
	src_id=$1
	case " $sourced_suites " in
		*" $src_id "*) return 0 ;;
	esac
	src_path=$(suite_file "$src_id")
	if [ -f "$src_path" ]; then
		# shellcheck disable=SC1090
		. "$src_path"
	fi
	sourced_suites="$sourced_suites $src_id"
}

has_fn() {
	type "$1" >/dev/null 2>&1
}

padded_prefix() {
	text=$1
	line="$text "
	while [ "${#line}" -lt "$status_col" ]; do
		line="${line}-"
	done
	case "$line" in
		*-) ;;
		*) line="${line}---" ;;
	esac
	printf '%s' "$line"
}

classify_status() {
	case_status=$1
	log=$2
	case_id=$3

	case "$case_status" in
		0)
			printf '%s\n' "PASS"
			return
			;;
		3)
			printf '%s\n' "TBD"
			return
			;;
		4)
			printf '%s\n' "BLOCKED"
			return
			;;
		2)
			if grep -qi 'not specified yet' "$log"; then
				printf '%s\n' "TBD"
			elif grep -qi 'cannot be run' "$log" ||
				grep -qi 'does not invent a tag' "$log" ||
				grep -qi 'assignment does not name' "$log" ||
				grep -qi 'missing test seam' "$log"; then
				printf '%s\n' "BLOCKED"
			else
				printf '%s\n' "MANUAL"
			fi
			return
			;;
		1)
			if grep -Eq "^${case_id} SETUP" "$log" ||
				grep -q 'The case cannot be run' "$log"; then
				printf '%s\n' "BLOCKED"
			else
				printf '%s\n' "FAIL"
			fi
			return
			;;
		*)
			printf '%s\n' "FAIL"
			;;
	esac
}

short_reason() {
	log=$1
	case_id=$2
	reason=$(grep -E '^error:' "$log" | tail -n 1)
	if [ -z "$reason" ]; then
		reason=$(grep -E "^${case_id}( SETUP| TEST STEPS|:)" "$log" | tail -n 1)
	fi
	if [ -z "$reason" ]; then
		reason=$(awk 'NF { line = $0 } END { print line }' "$log")
	fi
	printf '%s\n' "$reason" | awk '{
		s = $0
		if (length(s) > 160) s = substr(s, 1, 157) "..."
		print s
	}'
}

count_result() {
	cr=$1
	case "$cr" in
		PASS) pass_count=$((pass_count + 1)) ;;
		FAIL) fail_count=$((fail_count + 1)) ;;
		MANUAL) manual_count=$((manual_count + 1)) ;;
		TBD) tbd_count=$((tbd_count + 1)) ;;
		BLOCKED) blocked_count=$((blocked_count + 1)) ;;
		EV-001|REF) ref_count=$((ref_count + 1)) ;;
	esac
}

print_status_end() {
	printf '['
	print_colored_status "$1"
	printf ']\n'
}

write_case_status() {
	printf '%s\n' "$2" >"$log_dir/$1.status"
}

execute_function() {
	ex_fn=$1
	ex_id=$2
	ex_indent=$3
	ex_name=$4
	ex_count=$5

	cd "$repo_root" || return 1
	if [ -n "$ex_name" ]; then
		ex_label="$ex_indent$ex_id $ex_name"
	else
		ex_label="$ex_indent$ex_id"
	fi
	ex_prefix=$(padded_prefix "$ex_label")
	flush_print "$ex_prefix"

	mkdir -p "$log_dir"
	ex_log=$log_dir/$ex_id.log
	ex_rel=tmp/suit-runner/$ex_id.log
	"$ex_fn" >"$ex_log" 2>&1
	ex_rc=$?
	ex_result=$(classify_status "$ex_rc" "$ex_log" "$ex_id")
	print_status_end "$ex_result"
	write_case_status "$ex_id" "$ex_result"

	case "$ex_result" in
		FAIL|BLOCKED)
			printf '  %s%s\n' "$ex_indent" "$(short_reason "$ex_log" "$ex_id")"
			printf '  %slog: %s\n' "$ex_indent" "$ex_rel"
			;;
		MANUAL|TBD)
			printf '  %s%s\n' "$ex_indent" "$(short_reason "$ex_log" "$ex_id")"
			;;
	esac
	if [ "$ex_count" = "yes" ]; then
		count_result "$ex_result"
		displayed_count=$((displayed_count + 1))
	fi
}

record_missing() {
	ms_id=$1
	ms_indent=$2
	ms_name=$3
	ms_count=$4
	ms_why=${5:-no runner implementation}

	cd "$repo_root" || return 1
	if [ -n "$ms_name" ]; then
		ms_label="$ms_indent$ms_id $ms_name"
	else
		ms_label="$ms_indent$ms_id"
	fi
	ms_prefix=$(padded_prefix "$ms_label")
	flush_print "$ms_prefix"
	mkdir -p "$log_dir"
	ms_log=$log_dir/$ms_id.log
	printf '%s: %s\n' "$ms_id" "$ms_why" >"$ms_log"
	print_status_end "BLOCKED"
	write_case_status "$ms_id" "BLOCKED"
	printf '  %s%s\n' "$ms_indent" "$ms_why"
	printf '  %slog: tmp/suit-runner/%s.log\n' "$ms_indent" "$ms_id"
	if [ "$ms_count" = "yes" ]; then
		count_result "BLOCKED"
		displayed_count=$((displayed_count + 1))
	fi
}

run_leaf() {
	lf_id=$1
	lf_suite=$2
	lf_name=$3
	lf_indent=$4
	lf_count=$5

	source_suite "$lf_suite"
	lf_fn=$(id_to_fn "$lf_id")
	if has_fn "$lf_fn"; then
		execute_function "$lf_fn" "$lf_id" "$lf_indent" "$lf_name" "$lf_count"
	else
		record_missing "$lf_id" "$lf_indent" "$lf_name" "$lf_count" "no runner implementation"
	fi
}

status_rank() {
	case "$1" in
		FAIL) printf '%s\n' 5 ;;
		BLOCKED) printf '%s\n' 4 ;;
		TBD) printf '%s\n' 3 ;;
		MANUAL) printf '%s\n' 2 ;;
		EV-001|REF) printf '%s\n' 1 ;;
		PASS) printf '%s\n' 0 ;;
		*) printf '%s\n' 4 ;;
	esac
}

rank_to_status() {
	case "$1" in
		5) printf '%s\n' FAIL ;;
		4) printf '%s\n' BLOCKED ;;
		3) printf '%s\n' TBD ;;
		2) printf '%s\n' MANUAL ;;
		1) printf '%s\n' REF ;;
		*) printf '%s\n' PASS ;;
	esac
}

handle_pk_001() {
	pk_name=$1
	mkdir -p "$log_dir"
	if [ ! -f "$log_dir/EV-001.status" ]; then
		printf '%s\n' "  running EV-001 as PK-001 prerequisite"
		source_suite EV
		if has_fn ev_001; then
			execute_function ev_001 EV-001 "  " "prerequisite for PK-001" no
		else
			record_missing EV-001 "  " "prerequisite for PK-001" no "no runner implementation"
		fi
	fi
	pk_prereq=BLOCKED
	if [ -f "$log_dir/EV-001.status" ]; then
		pk_prereq=$(cat "$log_dir/EV-001.status")
	fi
	pk_label="PK-001 $pk_name"
	pk_prefix=$(padded_prefix "$pk_label")
	flush_print "$pk_prefix"
	pk_log=$log_dir/PK-001.log
	if [ "$pk_prereq" = "PASS" ]; then
		printf '%s\n' "PK-001: reference to EV-001. No separate execution. Not counted as PASS." >"$pk_log"
		print_status_end "EV-001"
		write_case_status PK-001 REF
		printf '  covered by EV-001 (no duplicate execution)\n'
		count_result REF
		displayed_count=$((displayed_count + 1))
	else
		printf '%s\n' "PK-001: EV-001 prerequisite is $pk_prereq" >"$pk_log"
		print_status_end "BLOCKED"
		write_case_status PK-001 BLOCKED
		printf '  EV-001 prerequisite is %s\n' "$pk_prereq"
		printf '  log: tmp/suit-runner/PK-001.log\n'
		count_result BLOCKED
		displayed_count=$((displayed_count + 1))
	fi
}

run_parent_with_variants() {
	pv_id=$1
	pv_suite=$2
	pv_name=$3
	printf '%s %s\n' "$pv_id" "$pv_name"
	pv_worst=0
	pv_mix=""
	pv_saw_pass=false
	pv_saw_other=false
	pv_tmp=$log_dir/$pv_id.variants
	catalogue_variants "$pv_id" "$pv_suite" >"$pv_tmp"
	while IFS='	' read -r pv_vid pv_vname; do
		[ -n "$pv_vid" ] || continue
		run_leaf "$pv_vid" "$pv_suite" "$pv_vname" "  " no
		pv_vresult=BLOCKED
		if [ -f "$log_dir/$pv_vid.status" ]; then
			pv_vresult=$(cat "$log_dir/$pv_vid.status")
		fi
		pv_rank=$(status_rank "$pv_vresult")
		if [ "$pv_rank" -gt "$pv_worst" ]; then
			pv_worst=$pv_rank
		fi
		if [ "$pv_vresult" = "PASS" ]; then
			pv_saw_pass=true
		else
			pv_saw_other=true
		fi
		if [ -n "$pv_mix" ]; then
			pv_mix="$pv_mix; $pv_vid $pv_vresult"
		else
			pv_mix="$pv_vid $pv_vresult"
		fi
	done <"$pv_tmp"
	pv_parent=$(rank_to_status "$pv_worst")
	if [ "$pv_saw_pass" = true ] && [ "$pv_saw_other" = true ] && [ "$pv_parent" = "PASS" ]; then
		pv_parent=BLOCKED
	fi
	pv_close=$(padded_prefix "  result")
	flush_print "$pv_close"
	print_status_end "$pv_parent"
	pv_unique=$(printf '%s\n' "$pv_mix" | awk '{
		n = split($0, a, "; ")
		first = ""
		mixed = 0
		for (i = 1; i <= n; i++) {
			split(a[i], b, " ")
			st = b[length(b)]
			if (first == "") first = st
			else if (st != first) mixed = 1
		}
		if (mixed) print "mixed"
	}')
	if [ "$pv_unique" = "mixed" ]; then
		printf '  mixed: %s\n' "$pv_mix"
	elif [ -n "$pv_mix" ]; then
		printf '  variants: %s\n' "$pv_mix"
	fi
	write_case_status "$pv_id" "$pv_parent"
	count_result "$pv_parent"
	displayed_count=$((displayed_count + 1))
}

run_catalogue_case() {
	cc_id=$1
	cc_suite=$2
	cc_name=$3

	if [ "$cc_id" = "PK-001" ]; then
		handle_pk_001 "$cc_name"
		return
	fi
	cc_vars=$(catalogue_variants "$cc_id" "$cc_suite")
	if [ -n "$cc_vars" ]; then
		run_parent_with_variants "$cc_id" "$cc_suite" "$cc_name"
		return
	fi
	run_leaf "$cc_id" "$cc_suite" "$cc_name" "" yes
}

run_suite() {
	run_id=$1
	if [ ! -f "$(suite_markdown "$run_id")" ]; then
		echo "error: missing suite catalogue: $(suite_markdown "$run_id")" >&2
		return 1
	fi
	suite_heading "$run_id"
	source_suite "$run_id"
	run_rows=$log_dir/$run_id.rows
	catalogue_rows "$run_id" >"$run_rows"
	while IFS='	' read -r run_cid run_cname; do
		[ -n "$run_cid" ] || continue
		run_catalogue_case "$run_cid" "$run_id" "$run_cname"
	done <"$run_rows"
}

run_one() {
	one_selector=$1
	one_suite=${one_selector%%-*}
	if [ ! -f "$(suite_markdown "$one_suite")" ]; then
		echo "error: unknown selector: $one_selector" >&2
		return 1
	fi
	case " $suites " in
		*" $one_suite "*) ;;
		*)
			echo "error: unknown selector: $one_selector" >&2
			return 1
			;;
	esac
	suite_heading "$one_suite"
	source_suite "$one_suite"

	case "$one_selector" in
		[A-Z][A-Z]-[0-9][0-9][0-9]-[A-Z])
			one_parent=${one_selector%-*}
			one_vname=$(catalogue_variants "$one_parent" "$one_suite" | awk -F '	' -v id="$one_selector" '$1==id { print $2; exit }')
			if [ -z "$one_vname" ]; then
				echo "error: unknown selector: $one_selector" >&2
				return 1
			fi
			run_leaf "$one_selector" "$one_suite" "$one_vname" "" yes
			;;
		[A-Z][A-Z]-[0-9][0-9][0-9])
			one_name=$(catalogue_rows "$one_suite" | awk -F '	' -v id="$one_selector" '$1==id { print $2; exit }')
			if [ -z "$one_name" ]; then
				echo "error: unknown selector: $one_selector" >&2
				return 1
			fi
			run_catalogue_case "$one_selector" "$one_suite" "$one_name"
			;;
		*)
			echo "error: unknown selector: $one_selector" >&2
			return 1
			;;
	esac
}

count_catalogue() {
	ct=0
	for ct_suite in $suites; do
		ct_n=$(catalogue_rows "$ct_suite" | wc -l)
		ct=$((ct + ct_n))
	done
	printf '%s\n' "$ct"
}

print_counts() {
	printf '\n'
	printf '%s\n' "PASS $pass_count"
	printf '%s\n' "FAIL $fail_count"
	printf '%s\n' "MANUAL $manual_count"
	printf '%s\n' "TBD $tbd_count"
	printf '%s\n' "BLOCKED $blocked_count"
	printf '%s\n' "REF $ref_count"
	printf '%s\n' "CATALOGUE $catalogue_total"
	printf '%s\n' "DISPLAYED $displayed_count"
}

if [ "$#" -ne 1 ] || [ -z "$1" ]; then
	usage
	exit 1
fi

if ! cd "$repo_root"; then
	echo "error: cannot cd to repository root: $repo_root" >&2
	exit 1
fi

mkdir -p "$log_dir"

selector=$(normalize_selector "$1")
case "$selector" in
	all)
		for suite_name in $suites; do
			if [ ! -f "$(suite_markdown "$suite_name")" ]; then
				echo "error: missing suite catalogue: $(suite_markdown "$suite_name")" >&2
				exit 1
			fi
		done
		catalogue_total=$(count_catalogue)
		for suite_name in $suites; do
			run_suite "$suite_name"
		done
		;;
	[A-Z][A-Z])
		case " $suites " in
			*" $selector "*)
				if [ ! -f "$(suite_markdown "$selector")" ]; then
					echo "error: missing suite catalogue: $(suite_markdown "$selector")" >&2
					exit 1
				fi
				catalogue_total=$(catalogue_rows "$selector" | awk 'END { print NR }')
				run_suite "$selector"
				;;
			*)
				echo "error: unknown selector: $selector" >&2
				exit 1
				;;
		esac
		;;
	[A-Z][A-Z]-[0-9][0-9][0-9]|[A-Z][A-Z]-[0-9][0-9][0-9]-[A-Z])
		suite_name=${selector%%-*}
		case " $suites " in
			*" $suite_name "*)
				catalogue_total=1
				run_one "$selector" || exit 1
				;;
			*)
				echo "error: unknown selector: $selector" >&2
				exit 1
				;;
		esac
		;;
	*)
		echo "error: unknown selector: $selector" >&2
		exit 1
		;;
esac

print_counts
if [ "$displayed_count" -ne "$catalogue_total" ] && [ "$selector" = "all" ]; then
	printf 'error: DISPLAYED %s does not match CATALOGUE %s\n' "$displayed_count" "$catalogue_total" >&2
	exit 1
fi
if [ "$fail_count" -ne 0 ] || [ "$blocked_count" -ne 0 ]; then
	exit 1
fi
exit 0
