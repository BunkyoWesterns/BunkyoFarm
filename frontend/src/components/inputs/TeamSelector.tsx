import { statusQuery, useTeamSolver } from "@/utils/queries"
import { Box, Combobox, TextInput, useCombobox } from "@mantine/core"
import { useEffect, useState } from "react"
import { CancelActionButton } from "@/components/elements/StatusIcon";

export const TeamSelector = ({ label, onChange }: { label?: string, onChange?: (team: number|undefined) => void }) => {
    const [team, setTeam] = useState<number|undefined>(undefined)
    const [value, setValue] = useState<string>("")
    const status = statusQuery()
    const teams = status.data?.teams??[]
    const teamSolver = useTeamSolver()
    const combobox = useCombobox();
    const filteredOptions = teams.filter((item) => JSON.stringify(item).toLowerCase().includes(value.toLowerCase().trim()))

    useEffect(() => {
        onChange?.(team)
        if (team == undefined) setValue("")
        else setValue(teamSolver(team))
    },[team])

    const options = [...filteredOptions.map((item) => (
            <Combobox.Option value={item.id.toString()} key={item.id}>
                {teamSolver(item.id)}
            </Combobox.Option>
        ))
    ];

    return <Box className="center-flex">
        <Combobox
            onOptionSubmit={(optionValue) => {
                setTeam(parseInt(optionValue));
                combobox.closeDropdown();
            }}
            store={combobox}
        >
        <Combobox.Target>
            <TextInput
            label={team==undefined?(label??"Select a team"): `Selected: ${teamSolver(team)}`}
            value={value}
            onChange={(event) => {
                setValue(event.target.value);
                combobox.openDropdown();
                combobox.updateSelectedOptionIndex();
            }}
            onClick={() => combobox.openDropdown()}
            onFocus={() => combobox.openDropdown()}
            onBlur={() => combobox.closeDropdown()}
            />
        </Combobox.Target>

        <Combobox.Dropdown>
            <Combobox.Options mah={250} style={{ overflowY: 'auto' }}>
            {options.length === 0 ? <Combobox.Empty>Nothing found</Combobox.Empty> : options}
            </Combobox.Options>
        </Combobox.Dropdown>
        </Combobox>
        <CancelActionButton disabled={team == undefined} onClick={() => setTeam(undefined)} />
  </Box>
}