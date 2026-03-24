import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import MarkdownWrapper from '../../../Markdown/MarkdownWrapper';
import styles from './TitleField.module.css';

interface TitleFieldProps {
    title?: string;
    description?: string;
    enableMarkdown?: boolean;
}

function TitleField({title, description, enableMarkdown = true}: TitleFieldProps) {
    // goal is for two \n to result in a separate <p>.
    const splitDesc = description?.split('\n\n').filter((s) => s !== '');

    return (
        <div className={styles['title-container']}>
            {title && <h2>{title}</h2>}
            {description && (
                <div className={styles['description-text']}>
                    {Object.values(splitDesc).map((d) => (
                        <p key={`${d}_${uniqueNumber()}`}>
                            {enableMarkdown ? (
                                <MarkdownWrapper>{d as string}</MarkdownWrapper>
                            ) : (
                                d
                            )}
                        </p>
                    ))}
                </div>
            )}
        </div>
    );
}

export default TitleField;
