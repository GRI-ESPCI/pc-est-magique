import { EditorState } from '@codemirror/state';
import { markdown } from '@codemirror/lang-markdown';
import { EditorView, ViewUpdate, highlightActiveLine, lineNumbers } from '@codemirror/view';
import { basicSetup } from 'codemirror';

// Wait for the DOM to be loaded before executing the script
document.addEventListener("DOMContentLoaded", () => {

    // Find all editors div on the page with id cm-editor-*
    const editors = document.querySelectorAll('[id ^= "cm-editor-"]');

    Array.prototype.forEach.call(editors, (e, i) => {
        const textarea = document.getElementById(e.id.substring(10, e.id.length)) as HTMLTextAreaElement;
        const initialValue = textarea.value;

        // Callback when the editor content is updated that update
        // the content of the textarea linked to it
        function onEditorChange(update: ViewUpdate) {
            if (update.docChanged) {
                textarea.innerHTML = update.state.doc.toString();
            }
        }

        // Theming
        const theme = EditorView.theme({
            "&": {height: "30em"},
            ".cm-scroller": {overflow: "auto"}
        });

        // Instantiate the code mirror editor inside the div
        const editor = new EditorView({
            parent: e,
            state: EditorState.create({
                extensions: [
                    basicSetup,
                    lineNumbers(),
                    highlightActiveLine(),
                    markdown(),
                    EditorView.updateListener.of(onEditorChange),
                    EditorView.lineWrapping,
                    theme
                ],
            })
        });

        // Intialize editor content with one from textarea
        editor.dispatch({
            changes: {from: 0, insert: initialValue}
        });
    });
});