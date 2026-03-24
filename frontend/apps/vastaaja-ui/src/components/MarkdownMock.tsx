import {ReactElement} from 'react';

// TODO: wondering if this is still needed when on vitest is in use

/**
 * Mock for MarkdownWrapper to stub it out from tests
 * @param children
 */
function MarkdownMock({children}: {children: ReactElement}) {
    return children;
}

export default MarkdownMock;
