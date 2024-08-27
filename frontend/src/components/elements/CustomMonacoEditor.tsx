import OneDarkPro from "@/monaco-theme/OneDarkProDarker.json"
import { Editor, type Monaco } from "@monaco-editor/react";

export const CustomMonacoEditor = (props:any) => {
    const handleEditorDidMount = (monaco: Monaco) => {
        monaco.editor.defineTheme("OneDarkPro",{
            base: "vs-dark",
            inherit: true,
            rules: [],
            ...OneDarkPro,
        });
    };
    return (
        <Editor
            language="python"
            width="100%"
            height="35vh"
            theme="OneDarkPro"
            beforeMount={handleEditorDidMount}
            options={{
                dragAndDrop: false
            }}
            {...(props??{})}
        />
    );
};