import { statsQuery, statusQuery } from "@/utils/queries";
import { Box, MantineStyleProp, ScrollArea, Space, Table } from "@mantine/core";
import { useMemo } from "react";
import { getDateFormatted } from "@/utils/time";
import { LineChartTeamsView } from "../LineChartTeamsView";
import { GlobalStat } from "@/utils/types";
import { AttackStatusIcon, FlagStatusIcon } from "../StatusIcon";

export const TeamsScreen = () => {

    const status = statusQuery()
    const stats = statsQuery()
    const thStyle: MantineStyleProp = { fontWeight: "bolder", fontSize: "130%", textTransform: "uppercase" } 

    const tickAggregatedData = useMemo(() => {
        return stats.data?.ticks.reduce((acc, tick) => {
            Object.keys(tick.teams).forEach((teamId) => {
                acc[teamId] = {
                    flags: {
                        ok: (tick.teams[teamId].flags.ok??0)+(acc[teamId]?.flags?.ok??0),
                        invalid: (tick.teams[teamId].flags.invalid??0)+(acc[teamId]?.flags?.invalid??0),
                        timeout: (tick.teams[teamId].flags.timeout??0)+(acc[teamId]?.flags?.timeout??0),
                        wait: (tick.teams[teamId].flags.wait??0)+(acc[teamId]?.flags?.wait??0),
                        tot: (tick.teams[teamId].flags.tot??0)+(acc[teamId]?.flags?.tot??0),
                    },
                    attacks: {
                        done: (tick.teams[teamId].attacks.done??0)+(acc[teamId]?.attacks?.done??0),
                        crashed: (tick.teams[teamId].attacks.crashed??0)+(acc[teamId]?.attacks?.crashed??0),
                        noflags: (tick.teams[teamId].attacks.noflags??0)+(acc[teamId]?.attacks?.noflags??0),
                        tot: (tick.teams[teamId].attacks.tot??0)+(acc[teamId]?.attacks?.tot??0),
                    }
                }
            })
            return acc
        }, {} as {[k:string]:GlobalStat|undefined})
    }, [stats.isFetching])??{}

    const tableData = useMemo(() => {
        return (status.data?.teams??[]).map((item) => {
            return <Table.Tr key={item.id} style={{fontSize:"120%"}}>
                <Table.Td>{item.id}</Table.Td>
                <Table.Td>{item.name??"-"}<br />{item.short_name??"-"}</Table.Td>
                <Table.Td>{item.host}</Table.Td>
                <Table.Td>
                    <Box display="flex">
                        <Box className="center-flex-col">
                            <FlagStatusIcon status="ok" disableTooltip /> {tickAggregatedData[item.id.toString()]?.flags.ok??0}
                        </Box>
                        <Space w="md" />
                        <Box className="center-flex-col">
                            <FlagStatusIcon status="invalid" disableTooltip /> {tickAggregatedData[item.id.toString()]?.flags.invalid??0}
                        </Box>
                        <Space w="md" />
                        <Box className="center-flex-col">
                            <FlagStatusIcon status="timeout" disableTooltip /> {tickAggregatedData[item.id.toString()]?.flags.timeout??0}
                        </Box>
                        <Space w="md" />
                        <Box className="center-flex-col">
                            <FlagStatusIcon status="wait" disableTooltip /> {tickAggregatedData[item.id.toString()]?.flags.wait??0}
                        </Box>
                    </Box>
                </Table.Td>
                <Table.Td>
                    <Box display="flex">
                        <Box className="center-flex-col">
                            <AttackStatusIcon status="done" disableTooltip /> {tickAggregatedData[item.id.toString()]?.attacks.done??0}
                        </Box>
                        <Space w="md" />
                        <Box className="center-flex-col">
                            <AttackStatusIcon status="noflags" disableTooltip /> {tickAggregatedData[item.id.toString()]?.attacks.noflags??0}
                        </Box>
                        <Space w="md" />
                        <Box className="center-flex-col">
                            <AttackStatusIcon status="crashed" disableTooltip /> {tickAggregatedData[item.id.toString()]?.attacks.crashed??0}
                        </Box>
                    </Box>
                </Table.Td>
                <Table.Td>{getDateFormatted(item.created_at)}</Table.Td>
            </Table.Tr>
        })
    }, [status.isFetching])
    
    return <Box style={{
        width: "100%",
    }}>
        <Box className="center-flex-col">
            <LineChartTeamsView withControls />
            <ScrollArea h="100%" w="100%">
                <Table>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th style={thStyle}>ID</Table.Th>
                            <Table.Th style={thStyle}>Name</Table.Th>
                            <Table.Th style={thStyle}>Host</Table.Th>
                            <Table.Th style={thStyle}>Flags</Table.Th>
                            <Table.Th style={thStyle}>Attacks</Table.Th>
                            <Table.Th style={thStyle}>Created At</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>{tableData}</Table.Tbody>
                </Table>
                <Space h="md" />
            </ScrollArea>
        </Box>
    </Box>
}