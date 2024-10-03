import { deleteService, exploitsQuery, statusQuery } from "@/utils/queries";
import { Box, Table, Title } from "@mantine/core";
import { DeleteButton, EditButton } from "@/components/inputs/Buttons";
import { Service } from "@/utils/types";
import { useState } from "react";
import { YesOrNoModal } from "@/components/modals/YesOrNoModal";
import { notifications } from "@mantine/notifications";
import { useQueryClient } from "@tanstack/react-query";
import { AddEditServiceModal } from "../modals/AddEditServiceModal";


export const ServiceTable = () => {

    const status = statusQuery()
    const services = status.data?.services??[]
    const exploits = exploitsQuery()

    const [deleteService, setDeleteService] = useState<Service|undefined>()
    const [editService, setEditService] = useState<Service|undefined>()


    const rows = services.map((srv) => {
        const exploitsAssociated = exploits.data?.filter((exp) => exp.service == srv.id)
        return <Table.Tr key={srv.id}>
            <Table.Td><Box>{srv.name}</Box></Table.Td>
            <Table.Td>{exploitsAssociated?.length}</Table.Td>
            <Table.Td><EditButton onClick={()=>setEditService(srv)} /></Table.Td>
            <Table.Td><DeleteButton onClick={()=>setDeleteService(srv)} /></Table.Td>
        </Table.Tr>
    });

    return <>
        <Table>
            <Table.Thead>
                <Table.Tr style={{fontSize: "120%"}}>
                    <Table.Th style={{width:"100%"}}>Name</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Exploits</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Edit</Table.Th>
                    <Table.Th style={{whiteSpace:"nowrap"}}>Delete</Table.Th>
                </Table.Tr>
            </Table.Thead>
            <Table.Tbody>{rows}</Table.Tbody>
        </Table>
        <Box className="center-flex" mt={10}>{rows.length == 0 && <Title order={4}>No services found</Title>}</Box>
        <DeleteServiceModal service={deleteService} onClose={()=>setDeleteService(undefined)} />
        <AddEditServiceModal service={editService} onClose={()=>setEditService(undefined)} edit />
    </>
}

export const DeleteServiceModal = ({ onClose, service }:{ onClose: () => void, service?: Service }) => {
    const queryClient = useQueryClient()

    return <YesOrNoModal
        open={ service != null }
        onClose={onClose}
        title={<Title order={3}>Deleting a service</Title>}
        onConfirm={()=>{
            if (service == null){
                onClose()
                return
            }
            deleteService(service?.id).then(()=>{
                notifications.show({ title: "Service deleted", message: `The service ${service?.name} has been deleted successfully`, color: "green" })
                queryClient.invalidateQueries({ queryKey: ["status"] })
                queryClient.resetQueries({ queryKey: ["exploits"] })
            }).catch((err)=>{
                notifications.show({ title: "Error deleting client", message: `An error occurred while deleting the service ${service?.name}: ${err.message}`, color: "red" })
            }).finally(()=>{ onClose() })
        }}
        size="xl"
        message={
        <>
            <span>Are you sure you want to delete the service <b>{service?.name}</b>?</span><br />
            <span style={{ color: "yellow" }}>This action could fail if the service has performed important actions on the platform!</span>
        </>
    }/>
}