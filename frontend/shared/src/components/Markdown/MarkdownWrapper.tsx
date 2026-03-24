import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import LaunchIcon from '@mui/icons-material/Launch';

interface MarkdownWrapperProps {
    children: string;
}

function CustomLink({href, children}) {
    return (
        <a href={href} target="_blank" rel="noreferrer">
            {children}
            <LaunchIcon fontVariant="externalLaunch" />
        </a>
    );
}

function MarkdownWrapper({children}: MarkdownWrapperProps) {
    /*  allow more elements
        strike trough 'del'
        cursive 'emphasis'
        bold 'strong'
    */
    return (
        <Markdown
            components={{a: CustomLink}}
            remarkPlugins={[remarkGfm]}
            allowedElements={['a']}
            unwrapDisallowed
        >
            {children}
        </Markdown>
    );
}

export default MarkdownWrapper;
