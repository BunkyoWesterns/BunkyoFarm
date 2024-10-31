import { Box, Container, Slider, Space, Text, Title } from "@mantine/core"
import { ClientTable } from "@/components/tables/ClientTable";
import { ServiceTable } from "../tables/ServiceTable";
import { ExploitTable } from "../tables/ExploitTable";
import { AddButton } from "../inputs/Buttons";
import { AddEditServiceModal } from "../modals/AddEditServiceModal";
import { useState } from "react";
import { useSettingsStore } from "@/utils/stores";
import { notifications } from "@mantine/notifications";

export const OptionScreen = () => {

    const [addNewServiceModalOpen, setAddNewServiceModalOpen] = useState(false)

    return <Container>
        <Title order={2}>
            Exploits
        </Title>
        <Space h="md" />
        <ExploitTable />
        <Space h="xl" />
        <Title order={2} display="flex" style={{alignItems: "center"}}>
            <span>Services</span><Box style={{flexGrow:1}} /><AddButton onClick={()=>setAddNewServiceModalOpen(true)} />
        </Title>
        <Space h="md" />
        <ServiceTable />
        <Space h="xl" />
        <Title order={2}>
            Clients
        </Title>
        <Space h="md" />
        <ClientTable />
        <Space h="xl" />
        <ViewOptionEditor />
        <AddEditServiceModal open={addNewServiceModalOpen} onClose={()=>setAddNewServiceModalOpen(false)} />
    </Container>
}


export const ViewOptionEditor = () => {
    const { setTablePageSize, tablePageSize } = useSettingsStore()
    return <Box>
        <Space h="md" />
        <Space h="xl" />
        <Slider
            min={5}
            max={300}
            step={5}
            label={(value) => value}
            defaultValue={tablePageSize}
            labelAlwaysOn
            marks={[
                { value: 5, label:"5" },
                { value: 30, label:"30" },
                { value: 60, label:"60" },
                { value: 100, label:"100" },
                { value: 150, label:"150" },
                { value: 200, label:"200" },
                { value: 300, label:"300" },
            ]}
            onChangeEnd={(value) => {
                setTablePageSize(value)
                notifications.show({
                    title: "Table size changed",
                    message: `New table size: ${value}`,
                    color: "blue",
                })
            }}
        />
        <Text size="sm" mt="xl">Tables size (bulk size on requests)</Text>
        <Space h="xl" /><Space h="md" />
    </Box>

}