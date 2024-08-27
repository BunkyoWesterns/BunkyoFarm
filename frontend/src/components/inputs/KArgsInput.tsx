import { KargsSubmitter } from "@/utils/types"
import { ComboboxItem, Select } from "@mantine/core"

export const typeDetailInfo = {
    str: "String",
    int: "Integer",
    float: "Float",
    bool: "Boolean",
}

export const KArgsTypeSelector = ({ value, onChange }:{ value: KargsSubmitter, onChange?: (value:KargsSubmitter|null, option:ComboboxItem)=>void }) => {
    const isStaticType = onChange == null
    let options = Object.keys(typeDetailInfo).map((type) => ({value:type, label:(typeDetailInfo as any)[type]}))
    if (!isStaticType){
        options = [
            ...options.filter((opt) => !["int", "float"].includes(opt.value)), {value:"float", label:"Number"},
        ]
    }

    return <Select
        data={options}
        value={value}
        onChange={(a,b)=>onChange?.(a as KargsSubmitter, b)}
        disabled={isStaticType}
    />

}