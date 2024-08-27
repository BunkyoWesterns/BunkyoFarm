import { statsQuery, statusQuery } from "@/utils/queries";
import { Box, Checkbox, MantineStyleProp, ScrollArea, Space, Table } from "@mantine/core";
import { useMemo, useState } from "react";
import { LineChartTeamsView } from "@/components/charts/LineChartTeamsView";
import { GlobalStat } from "@/utils/types";
import { AttackStatusIcon, FlagStatusIcon } from "@/components/elements/StatusIcon";

export const TeamsScreen = () => {

    const status = statusQuery()
    const stats = statsQuery()
    const thStyle: MantineStyleProp = { fontWeight: "bolder", fontSize: "130%", textTransform: "uppercase" }
    const [selectedRows, setSelectedRows] = useState<number[]>(status.data?.teams?.map((team) => team.id)??[]);

    const tickAggregatedData = useMemo(() => {
        return stats.data?.ticks.reduce((acc, tick) => {
            Object.keys(tick.teams).forEach((teamId) => {
                acc[teamId] = {
                    flags: {
                        ok: (tick.teams[teamId]?.flags.ok??0)+(acc[teamId]?.flags?.ok??0),
                        invalid: (tick.teams[teamId]?.flags.invalid??0)+(acc[teamId]?.flags?.invalid??0),
                        timeout: (tick.teams[teamId]?.flags.timeout??0)+(acc[teamId]?.flags?.timeout??0),
                        wait: (tick.teams[teamId]?.flags.wait??0)+(acc[teamId]?.flags?.wait??0),
                        tot: (tick.teams[teamId]?.flags.tot??0)+(acc[teamId]?.flags?.tot??0),
                    },
                    attacks: {
                        done: (tick.teams[teamId]?.attacks.done??0)+(acc[teamId]?.attacks?.done??0),
                        crashed: (tick.teams[teamId]?.attacks.crashed??0)+(acc[teamId]?.attacks?.crashed??0),
                        noflags: (tick.teams[teamId]?.attacks.noflags??0)+(acc[teamId]?.attacks?.noflags??0),
                        tot: (tick.teams[teamId]?.attacks.tot??0)+(acc[teamId]?.attacks?.tot??0),
                    }
                }
            })
            return acc
        }, {} as {[k:string]:GlobalStat|undefined})
    }, [stats.isFetching])??{}

    const countersWidth = 32

    const tableData = useMemo(() => {
        return (status.data?.teams??[]).map((item) => {
            return <Table.Tr key={item.id} style={{fontSize:"120%"}}>
                <Table.Td>
                    <Checkbox
                        aria-label="Select row"
                        checked={selectedRows.includes(item.id)}
                        onChange={(event) =>
                            setSelectedRows(
                            event.currentTarget.checked
                                ? [...selectedRows, item.id]
                                : selectedRows.filter((position) => position !== item.id)
                            )
                        }
                    />
                </Table.Td>
                <Table.Td><Box>{item.id}</Box></Table.Td>
                <Table.Td><Box>{item.name??"-"}<br />{item.short_name??"-"}</Box></Table.Td>
                <Table.Td><Box>{item.host}</Box></Table.Td>
                <Table.Td>
                    <Box display="flex" className="center-flex">
                        <Box className="center-flex-col" style={{ width: countersWidth }}>
                            <FlagStatusIcon status="ok" disableTooltip /> {tickAggregatedData[item.id.toString()]?.flags.ok??0}
                        </Box>
                        <Space w="xs" />
                        <Box className="center-flex-col" style={{ width: countersWidth }}>
                            <FlagStatusIcon status="invalid" disableTooltip /> {tickAggregatedData[item.id.toString()]?.flags.invalid??0}
                        </Box>
                        <Space w="xs" />
                        <Box className="center-flex-col" style={{ width: countersWidth }}>
                            <FlagStatusIcon status="timeout" disableTooltip /> {tickAggregatedData[item.id.toString()]?.flags.timeout??0}
                        </Box>
                        <Space w="xs" />
                        <Box className="center-flex-col" style={{ width: countersWidth }}>
                            <FlagStatusIcon status="wait" disableTooltip /> {tickAggregatedData[item.id.toString()]?.flags.wait??0}
                        </Box>
                    </Box>
                </Table.Td>
                <Table.Td className="center-flex">
                    <Box display="flex">
                        <Box className="center-flex-col" style={{ width: countersWidth }}>
                            <AttackStatusIcon status="done" disableTooltip /> {tickAggregatedData[item.id.toString()]?.attacks.done??0}
                        </Box>
                        <Space w="xs" />
                        <Box className="center-flex-col" style={{ width: countersWidth }}>
                            <AttackStatusIcon status="noflags" disableTooltip /> {tickAggregatedData[item.id.toString()]?.attacks.noflags??0}
                        </Box>
                        <Space w="xs" />
                        <Box className="center-flex-col" style={{ width: countersWidth }}>
                            <AttackStatusIcon status="crashed" disableTooltip /> {tickAggregatedData[item.id.toString()]?.attacks.crashed??0}
                        </Box>
                    </Box>
                </Table.Td>
            </Table.Tr>
        })
    }, [status.isFetching, selectedRows])
    
    return <Box style={{
        width: "100%",
    }}>
        <Box className="center-flex-col">
            <LineChartTeamsView withControls teamsList={selectedRows} />
            <ScrollArea h="100%" w="100%">
                <Table>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th style={thStyle}>
                                <Checkbox
                                    aria-label="Select row"
                                    checked={selectedRows.length === (status.data?.teams?.length??0)}
                                    onChange={(event) =>
                                        setSelectedRows(
                                            event.currentTarget.checked
                                            ? (status.data?.teams??[]).map((team) => team.id) : []
                                        )
                                    }
                                />
                            </Table.Th>
                            <Table.Th style={thStyle}>ID</Table.Th>
                            <Table.Th style={thStyle}>Name</Table.Th>
                            <Table.Th style={thStyle}>Host</Table.Th>
                            <Table.Th style={thStyle}><Box className="center-flex">Flags</Box></Table.Th>
                            <Table.Th style={thStyle}><Box className="center-flex">Attacks</Box></Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>{tableData}</Table.Tbody>
                </Table>
                <Space h="md" />
            </ScrollArea>
        </Box>
    </Box>
}