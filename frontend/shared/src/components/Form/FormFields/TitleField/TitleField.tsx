import styles from './TitleField.module.css';

interface TitleFieldProps {
    title?: string;
    description?: string;
}

function TitleField({title, description}: TitleFieldProps) {
    return (
        <div className={styles['title-container']}>
            {title && <h2>{title}</h2>}
            {description && (
                <div className={styles['description-text']}>{description}</div>
            )}
        </div>
    );
}

export default TitleField;
