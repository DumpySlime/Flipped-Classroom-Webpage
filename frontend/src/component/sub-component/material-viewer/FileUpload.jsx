import { Fragment, useState, useEffect } from 'react'

function FileUpload (props) {

    useEffect(() => {
        clearFileUpload()
    }, [])

    const [fileName, setFileName] = useState('')
    const [fileSize, setFileSize] = useState('')
    const [fileSizeKB, setFileSizeKB] = useState('')
    const [fileType, setFileType] = useState('')
    const [src, setSrc] = useState('')
 

    const clearFileUpload = () => {
        setFileName('')
        setFileSize('')
        setFileType('')
        setSrc('')
        props.dataChanger('')
    }

    const onFilePicked = (e) => {
        let file = e.target.files[0];

        let file_name = file.name;
        let file_size = getFileSize(file.size);
        let file_size_kb = getFileSizeKB(file.size);
        let file_type = getFileType(file).toLowerCase();

        setFileName(file_name)
        setFileSize(file_size)
        setFileSizeKB(file_size_kb)
        setFileType(file_type)

        if (props?.max_file_size_in_kb &&  file_size_kb > props?.max_file_size_in_kb) 
        {
            alert('Maximum allowed file size = '+props?.max_file_size_in_kb+ ' kb')
            clearFileUpload()
            return false;
        }

        if (props?.allowed_extensions && !arrToLowerCase(props?.allowed_extensions).includes(file_type)) 
        {
            clearFileUpload()
            alert(`Allowed file type = ${props.allowed_extensions.join(', ')}`)
            return false;
        }
        
        props.dataChanger(file);
    }

    const getFileSize = (file_size) =>
    {
        if ( (file_size/1024) >= 1024 )
        {
            file_size= parseInt((file_size/1024)/1024) + ' MB';
        }
        else{
            file_size=parseInt(file_size/1024) + ' KB';
        }
        return file_size;
    }

    const getFileSizeKB = (file_size) =>
    {
        file_size=parseInt(file_size/1024);
        return file_size;
    }


    const getFileType = (file) =>
    {
        const fileName = file?.name || '';
        return fileName.split('.').pop().toLowerCase();
    }

    const arrToLowerCase = (arr=[]) => {
        return arr.map(str => str.toLowerCase());
    }


    return (
        <Fragment>
        {fileName && (
            <div>
                <strong>{fileName}</strong> ({fileSize})
                <button type="button" onClick={clearFileUpload}>✕</button>
            </div>
        )}
        <br />
        <input 
            className="file d-none" 
            type="file"
            id={props?.name} 
            name={props?.name}
            required={props?.required || false} 
            onChange={onFilePicked}
            accept={props?.allowed_extensions?.map(ext => `.${ext}`).join(',')}
        /> 
    </Fragment>
    )
}

export default FileUpload;