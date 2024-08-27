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
    return <Select
        data={Object.keys(typeDetailInfo).map((type) => ({value:type, label:(typeDetailInfo as any)[type]}))}
        value={value}
        onChange={(a,b)=>onChange?.(a as KargsSubmitter, b)}
        disabled={isStaticType}
    />

}