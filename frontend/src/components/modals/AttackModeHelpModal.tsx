import { Box, Modal, Space, Title } from "@mantine/core"
import { AttackModeIcon } from "../elements/StatusIcon";

export const AttackModeHelpModal = ({ open, onClose }:{ open:boolean, onClose:()=>void}) => {

    return <Modal opened={open} onClose={onClose} title="Attack stategy help 💬" size="xl" centered>
        <Title order={3}>What are attack strategy?</Title>
        <p>
            Attack strategy defines when and with what timimg the attacks should be triggered. 
            ExploitFarm offers 3 types of attack mode, described better below
        </p>
        <Box display="flex">
            <Title order={3}>1. Tick delay</Title>
            <Space w="xs" />
            <AttackModeIcon status="tick-delay" disableTooltip />
        </Box>
        <p>
            Tick delay attacks starts with a delay of 1 tick, this timing is indipendent
            from the real tick time and between each attack (attacks are triggered in different moments)
        </p>
        <Box display="flex">
            <Title order={3}>2. Loop Attack</Title>
            <Space w="xs" />
            <AttackModeIcon status="loop-delay" disableTooltip />
        </Box>
        <p>
            Loop attack is similar to tick delay, but in this case you can set a custom delay indipedent from the tick time.
            You can also set this delay to 0 to loop the attack as fast as possible (not recommended, organization may ban you and you pc become warm)
        </p>
        <Box display="flex">
            <Title order={3}>3. Tick time</Title>
            <Space w="xs" />
            <AttackModeIcon status="wait-for-time-tick" disableTooltip />
        </Box>
        <p>
            Tick time is a syncronized attack based on game start time (you must define START_TIME to use this attack mode), where the attacks are triggere at the beginning of each tick.
            You can even set a custom initial delay from the start of the tick (in seconds), before all the attacks will be triggered.
            The first attack of an xfarm instance is always triggered, and be triggered again at the start of next the tick.
        </p>
    </Modal>
}