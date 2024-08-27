import { clientsQuery, deleteClient, exploitsQuery } from "@/utils/queries";
import { getDateFormatted } from "@/utils/time";
import { Box, Table, Title } from "@mantine/core";
import { DeleteButton } from "@/components/inputs/Buttons";
import { Clinet } from "@/utils/types";
import { Fragment, useState } from "react";
import { YesOrNoModal } from "@/components/modals/YesOrNoModal";
import { notifications } from "@mantine/notifications";
import { useQueryClient } from "@tanstack/react-query";


export const ClientTable = () => {

    const clients = clientsQuery()
    const exploits = exploitsQuery()

    const [deleteClient, setDeleteClient] = useState<Clinet|undefined>()

    const rows = clients.data?.map((client) => {
        if (client.id == "manual") return <Fragment key="null"></Fragment>
        const activeExploits = exploits.data?.reduce((oldCount, nextExpl)=>((nextExpl.last_execution_by == client.id && nextExpl.status == "active")?oldCount+1: oldCount), 0)
        const disabledExploits = exploits.data?.reduce((oldCount, nextExpl)=>((nextExpl.last_execution_by == client.id && nextExpl.status == "disabled")?oldCount+1: oldCount), 0)
        return <Table.Tr key={client.id}>
            <Table.Td style={{width:"100%"}}><Box>{client.name}</Box></Table.Td>
            <Table.Td><Box>{activeExploits??0}</Box></Table.Td>
            <Table.Td><Box>{disabledExploits??0}</Box></Table.Td>
            <Table.Td><Box>{getDateFormatted(client.created_at)}</Box></Table.Td>
            <Table.Td><DeleteButton onClick={()=>setDeleteClient(client)} /></Table.Td>
        </Table.Tr>
    });

    return <>
        <Table>
            <Table.Thead>
                <Table.Tr style={{fontSize: "120%"}}>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Name</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Running exploits</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Inactive Exploits</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Created At</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Delete</Table.Th>
                </Table.Tr>
            </Table.Thead>
            <Table.Tbody>{rows}</Table.Tbody>
        </Table>
        <DeleteClientModal client={deleteClient} onClose={()=>setDeleteClient(undefined)} />
    </>
}

export const DeleteClientModal = ({ onClose, client }:{ onClose: () => void, client?: Clinet }) => {
    const queryClient = useQueryClient()

    return <YesOrNoModal
        open={ client != null }
        onClose={onClose}
        title={<Title order={3}>Deleting a client</Title>}
        onConfirm={()=>{
            if (client == null){
                onClose?.()
                return
            }
            deleteClient(client?.id).then(()=>{
                notifications.show({ title: "Client deleted", message: `The client ${client?.name} has been deleted successfully`, color: "green" })
                queryClient.invalidateQueries({ queryKey: ["clients"] })
            }).catch((err)=>{
                notifications.show({ title: "Error deleting client", message: `An error occurred while deleting the client ${client?.name}: ${err.message}`, color: "red" })
            }).finally(()=>{ onClose() })
        }}
        size="xl"
        message={
        <>
            <span>Are you sure you want to delete the client <b>{client?.name}</b>?</span><br />
            <span style={{ color: "yellow" }}>This action could fail if the client has performed important actions on the platform!</span>
        </>
    }/>
}