import { groupsQuery, useClientSolver, useExtendedExploitSolver } from "@/utils/queries";
import { getDateSmallFormatted } from "@/utils/time";
import { Box, Table, Title } from "@mantine/core";
import { DeleteButton, EditButton } from "@/components/inputs/Buttons";
import { AttackGroup } from "@/utils/types";
import { useState } from "react";
import { StatusPoint } from "../elements/ExploitsBar";
import { DeleteGroupModal } from "../modals/DeleteGroupModal";
import { EditGroupModal } from "../modals/EditGroupModal";


export const GroupTable = () => {

    const groups = groupsQuery()
    const getClientName = useClientSolver()
    const exploitSolver = useExtendedExploitSolver()

    const [deleteGroup, setDeleteGroup] = useState<AttackGroup|undefined>()
    const [editGroup, setEditGroup] = useState<AttackGroup|undefined>()



    const rows = groups.data?.map((grp) => {
        return <Table.Tr key={grp.id}>
            <Table.Td><StatusPoint status={grp.status} /></Table.Td>
            <Table.Td style={{width:"100%"}}><Box>{grp.name}</Box></Table.Td>
            <Table.Td><Box>{grp.members.map(ele => getClientName(ele)).join(", ")}</Box></Table.Td>
            <Table.Td><Box>{exploitSolver(grp.exploit)}</Box></Table.Td>
            <Table.Td><Box>{grp.commit}</Box></Table.Td>
            <Table.Td><Box>{grp.last_attack_at?getDateSmallFormatted(grp.last_attack_at):"Never started"}</Box></Table.Td>
            <Table.Td><EditButton onClick={()=>setEditGroup(grp)} /></Table.Td>
            <Table.Td><DeleteButton onClick={()=>setDeleteGroup(grp)} /></Table.Td>
        </Table.Tr>
    })??[];

    return <>
        <Table>
            <Table.Thead>
                <Table.Tr style={{fontSize: "120%"}}>
                    <Table.Th style={{whiteSpace:"nowrap"}}><StatusPoint /></Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Name</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Members</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Exploit</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Commit</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Last Execution</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Edit</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Delete</Table.Th>
                </Table.Tr>
            </Table.Thead>
            <Table.Tbody>{rows}</Table.Tbody>
        </Table>
        <Box className="center-flex" mt={10}>{rows.length == 0 && <Title order={4}>No group found</Title>}</Box>
        <DeleteGroupModal group={deleteGroup} onClose={()=>setDeleteGroup(undefined)} />
        <EditGroupModal group={editGroup} onClose={()=>setEditGroup(undefined)} />
    </>
}

