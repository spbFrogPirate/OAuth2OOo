package io.github.prrvchr.uno.helper;

import java.lang.Exception;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.MalformedURLException;
import java.net.URL;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.Map;
import java.util.Properties;

import com.sun.star.beans.Property;
import com.sun.star.beans.PropertyValue;
import com.sun.star.deployment.XPackageInformationProvider;
import com.sun.star.lang.IllegalArgumentException;
import com.sun.star.lang.WrappedTargetException;
import com.sun.star.lang.XMultiComponentFactory;
import com.sun.star.sdbc.DriverPropertyInfo;
import com.sun.star.sdbc.SQLException;
import com.sun.star.sdbc.XArray;
import com.sun.star.sdbc.XBlob;
import com.sun.star.sdbc.XClob;
import com.sun.star.uno.Any;
import com.sun.star.uno.AnyConverter;
import com.sun.star.uno.Type;
import com.sun.star.uno.UnoRuntime;
import com.sun.star.uno.XComponentContext;
import com.sun.star.uno.XInterface;
import com.sun.star.util.Date;
import com.sun.star.util.DateTime;
import com.sun.star.util.Time;


public class UnoHelper
{

	public static Object createService(XComponentContext context, String identifier)
	{
		Object service = null;
		try
		{
			XMultiComponentFactory manager = context.getServiceManager();
			service = manager.createInstanceWithContext(identifier, context);
		}
		catch (Exception e) { e.printStackTrace(); }
		return service;
	}


	public static String getPackageLocation(XComponentContext context, String identifier, String path)
	{
		String location = getPackageLocation(context, identifier);
		return location + "/" + path + "/";
	}


	public static String getPackageLocation(XComponentContext context, String identifier)
	{
		String location = "";
		XPackageInformationProvider xProvider = null;
		try
		{
			Object oProvider = context.getValueByName("/singletons/com.sun.star.deployment.PackageInformationProvider");
			xProvider = (XPackageInformationProvider) UnoRuntime.queryInterface(XPackageInformationProvider.class, oProvider);
		}
		catch (Exception e) { e.printStackTrace(); }
		if (xProvider != null) location = xProvider.getPackageLocation(identifier);
		return location;
	}


	public static URL getDriverURL(String location, String jar)
	{
		URL url = null;
		try
		{
			url = new URL("jar:" + location + jar + "!/");
		}
		catch (Exception e) { e.printStackTrace(); }
		return url;
	}


	public static URL getDriverURL(String location, String path, String jar)
	throws MalformedURLException
	{
		URL url = new URL("jar:" + location + "/" + path + "/" + jar + "!/");
		return url;
	}


	public static DriverPropertyInfo[] getDriverPropertyInfos()
	{
		ArrayList<DriverPropertyInfo> infos = new ArrayList<>();
		DriverPropertyInfo info1 = getDriverInfo("AutoIncrementCreation",
                                                 "GENERATED BY DEFAULT AS IDENTITY");
		infos.add(0, info1);
		DriverPropertyInfo info2 = getDriverInfo("AutoRetrievingStatement",
                                                 "CALL IDENTITY()");
		infos.add(0, info2);
		int len = infos.size();
		return infos.toArray(new DriverPropertyInfo[len]);
	}


	public static DriverPropertyInfo getDriverInfo(String name, String value)
	{
		DriverPropertyInfo info = new DriverPropertyInfo();
		info.Name = name;
		info.Value = value;
		info.IsRequired = true;
		info.Choices = new String[0];
		return info;
	}


	public static Properties getConnectionProperties(PropertyValue[] infos)
	{
		System.out.println("UnoHelper.getProperties() 1 ");
		Properties properties = new Properties();
		int len = infos.length;
		for (int i = 0; i < len; i++)
		{
			PropertyValue info = infos[i];
			String value = String.valueOf(info.Value);
			// FIXME: JDBC doesn't seem to like <Properties> with empty values!!!
			if (!value.isEmpty()) properties.setProperty(info.Name, value);
		}
		System.out.println("UnoHelper.getProperties() 2 " + properties);
		return properties;
	}


	public static Property getProperty(String name, String type)
	{
		short attributes = 0;
		return getProperty(name, type, attributes);
	}


	public static Property getProperty(String name, String type, short attributes)
	{
		int handle = -1;
		return getProperty(name, handle, type, attributes);
	}


	public static Property getProperty(String name, int handle, String type, short attributes)
	{
		Property property = new Property();
		property.Name = name;
		property.Handle = handle;
		property.Type = new Type(type);
		property.Attributes = attributes;
		return property;
	}

	public static java.sql.SQLException getSQLException(Exception e)
	{
		return new java.sql.SQLException(e.getMessage(), e);
	}
	
	
	public static SQLException getSQLException(java.sql.SQLException e, XInterface component)
	{
		SQLException exception = null;
		if (e != null)
		{
			String message = e.getMessage();
			exception = new SQLException(message);
			exception.Context = component;
			exception.SQLState = e.getSQLState();
			exception.ErrorCode = e.getErrorCode();
			exception.NextException = getSQLException(e.getNextException(), component);
		}
		return exception;
	}


	public static String getObjectString(Object object)
	{
		String value = "";
		if (AnyConverter.isString(object))
		{
			value = AnyConverter.toString(object);
		}
		return value;
	}


	public static Date getUnoDate(java.sql.Date date)
	{
		LocalDate localdate = date.toLocalDate();
		Date value = new Date();
		value.Year = (short) localdate.getYear();
		value.Month = (short) localdate.getMonthValue();
		value.Day = (short) localdate.getDayOfMonth();
		return value;
	}


	public static java.sql.Date getJavaDate(Date date)
	{
		LocalDate localdate = LocalDate.of(date.Year, date.Month, date.Day);
		return java.sql.Date.valueOf(localdate);
	}


	public static Time getUnoTime(java.sql.Time time)
	{
		LocalTime localtime = time.toLocalTime();
		Time value = new Time();
		value.Hours = (short) localtime.getHour();
		value.Minutes = (short) localtime.getMinute();
		value.Seconds = (short) localtime.getSecond();
		value.NanoSeconds = localtime.getNano();
		//value.HundredthSeconds = 0;
		return value;
	}


	public static java.sql.Time getJavaTime(Time time)
	{
		LocalTime localtime = LocalTime.of(time.Hours, time.Minutes, time.Seconds, time.NanoSeconds);
		return java.sql.Time.valueOf(localtime);
	}


	public static DateTime getUnoDateTime(java.sql.Timestamp timestamp)
	{
		LocalDateTime localdatetime = timestamp.toLocalDateTime();
		DateTime value = new DateTime();
		value.Year = (short) localdatetime.getYear();
		value.Month = (short) localdatetime.getMonthValue();
		value.Day = (short) localdatetime.getDayOfMonth();
		value.Hours = (short) localdatetime.getHour();
		value.Minutes = (short) localdatetime.getMinute();
		value.Seconds = (short) localdatetime.getSecond();
		value.NanoSeconds = localdatetime.getNano();
		//value.HundredthSeconds = 0;
		return value;
	}


	public static java.sql.Timestamp getJavaDateTime(DateTime timestamp)
	{
		LocalDateTime localdatetime = LocalDateTime.of(timestamp.Year, timestamp.Month, timestamp.Day, timestamp.Hours, timestamp.Minutes, timestamp.Seconds, timestamp.NanoSeconds);
		return java.sql.Timestamp.valueOf(localdatetime);
	}


	public static Object getObjectFromResult(java.sql.ResultSet result, int index)
	{
		Object value = null;
		try
		{
			value = result.getObject(index);
		}
		catch (java.sql.SQLException e) {e.getStackTrace();}
		return value;
	}


	public static String getResultSetValue(java.sql.ResultSet result, int index)
	{
		String value = null;
		try
		{
			value = result.getString(index);
		}
		catch (java.sql.SQLException e) {e.getStackTrace();}
		return value;
	}


	public static Object getValueFromResult(java.sql.ResultSet result, int index)
	{
		// TODO: 'TINYINT' is buggy: don't use it
		Object value = null;
		try
		{
			String dbtype = result.getMetaData().getColumnTypeName(index);
			if (dbtype == "VARCHAR")
			{
				value = result.getString(index);
			}
			else if (dbtype == "BOOLEAN")
			{
				value = result.getBoolean(index);
			}
			else if (dbtype == "TINYINT"){
				value = result.getShort(index);
			}
			else if (dbtype == "SMALLINT"){
				value = result.getShort(index);
			}
			else if (dbtype == "INTEGER"){
				value = result.getInt(index);
			}
			else if (dbtype == "BIGINT"){
				value = result.getLong(index);
			}
			else if (dbtype == "FLOAT"){
				value = result.getFloat(index);
			}
			else if (dbtype == "DOUBLE"){
				value = result.getDouble(index);
			}
			else if (dbtype == "TIMESTAMP"){
				value = result.getTimestamp(index);
			}
			else if (dbtype == "TIME"){
				value = result.getTime(index);
			}
			else if (dbtype == "DATE"){
				value = result.getDate(index);
			}
		}
		catch (java.sql.SQLException e) {e.getStackTrace();}
		return value;
	}


	public static java.sql.Array getSQLArray(java.sql.Statement statement, XArray array)
	throws java.sql.SQLException, SQLException
	{
		String type = array.getBaseTypeName();
		Object[] value = array.getArray(null);
		return statement.getConnection().createArrayOf(type, value);
	}


	public static java.sql.Clob getSQLClob(java.sql.Statement statement, XClob clob)
	throws java.sql.SQLException, SQLException
	{
		System.out.println("UnoHelper.getJavaClob() 1");
		String value = clob.toString();
		System.out.println("UnoHelper.getJavaClob() 2");
		java.sql.Clob c = statement.getConnection().createClob();
		c.setString(1, value);
		System.out.println("UnoHelper.getJavaClob() 3");
		return c;
	}


	public static java.sql.Blob getSQLBlob(java.sql.Statement statement, XBlob blob)
	throws java.sql.SQLException, SQLException
	{
		System.out.println("UnoHelper.getJavaBlob() 1");
		int len = (int) blob.length();
		byte[] value = blob.getBytes(1, len);
		System.out.println("UnoHelper.getJavaBlob() 2");
		java.sql.Blob b = statement.getConnection().createBlob();
		b.setBytes(1, value);
		System.out.println("UnoHelper.getJavaBlob() 3");
		return b;
	}


	public static Integer getConstantValue(Class<?> clazz, String name)
	throws java.sql.SQLException
	{
		try {
			return (int) clazz.getDeclaredField(name).get(null);
		} catch (IllegalArgumentException | IllegalAccessException | NoSuchFieldException | SecurityException e) {
			e.printStackTrace();
			throw getSQLException(e);
		}
	}


	public static String mapSQLDataType(int key, String name)
	{
		Map<Integer, String> maps = Map.ofEntries(Map.entry(2003, "ARRAY"),
												  Map.entry(70, "OTHER"),
												  Map.entry(2000, "OBJECT"),
												  Map.entry(-16, "LONGVARCHAR"),
												  Map.entry(-15, "CHAR"),
												  Map.entry(2011, "CLOB"),
												  Map.entry(0, "SQLNULL"),
												  Map.entry(-9, "VARCHAR"),
												  Map.entry(2012, "REF"),
												  Map.entry(-8, "INTEGER"),
												  Map.entry(2009, "OTHER"),
												  Map.entry(2013, "VARCHAR"),
												  Map.entry(2014, "VARCHAR"));
		return (maps.containsKey(key)) ? maps.get(key) : name;
	}


	// com.sun.star.lib.uno.helper.PropertySet:
	public static boolean convertPropertyValue(Property property,
											   Object[] newValue,
											   Object[] oldValue,
											   Object value,
											   Object object,
											   Object id)
	throws com.sun.star.lang.IllegalArgumentException,
		   com.sun.star.lang.WrappedTargetException
	{
		oldValue[0] = getPropertyValue(property, object, id);
		Class<?> clazz = property.Type.getZClass();
		boolean voidvalue = false;
		boolean anyvalue = value instanceof Any;
		if (anyvalue) voidvalue = ((Any) value).getObject() == null;
		else voidvalue = value == null;
		if (voidvalue && clazz.isPrimitive())
			throw new com.sun.star.lang.IllegalArgumentException("The implementation does not support the MAYBEVOID attribute for this property");
		Object converted = null;
		if (clazz.equals(Any.class))
		{
			if (anyvalue) converted = value;
			else
			{
				if (value instanceof XInterface)
				{
					XInterface xInt = UnoRuntime.queryInterface(XInterface.class, value);
					if (xInt != null) converted = new Any(new Type(XInterface.class), xInt);
				}
				else if (value == null)
				{
					if (oldValue[0] == null) converted = new Any(new Type(), null);
					else converted = new Any(((Any)oldValue[0]).getType(), null);
				}
				else converted = new Any(new Type(value.getClass()), value);
			}
		}
		else converted = convert(clazz, value);
		newValue[0] = converted;
		return true;
	}

	@SuppressWarnings("deprecation")
	private static Object convert(Class<?> clazz, Object object)
	throws com.sun.star.lang.IllegalArgumentException
	{
		Object value = null;
		if (object == null || (object instanceof Any && ((Any) object).getObject() == null)) value = null;
		else if (clazz.equals(Object.class))
		{
			if (object instanceof Any) object = ((Any) object).getObject();
			value = object;
		}
		else if (clazz.equals(boolean.class)) value = new Boolean(AnyConverter.toBoolean(object));
		else if (clazz.equals(char.class)) value = new Character(AnyConverter.toChar(object));
		else if (clazz.equals(byte.class)) value = new Byte(AnyConverter.toByte(object));
		else if (clazz.equals(short.class)) value = new Short(AnyConverter.toShort(object));
		else if (clazz.equals(int.class)) value = new Integer(AnyConverter.toInt(object));
		else if (clazz.equals(long.class)) value = new Long(AnyConverter.toLong(object));
		else if (clazz.equals(float.class)) value = new Float(AnyConverter.toFloat(object));
		else if (clazz.equals(double.class)) value = new Double(AnyConverter.toDouble(object));
		else if (clazz.equals(String.class)) value = AnyConverter.toString(object);
		else if (clazz.isArray()) value = AnyConverter.toArray(object);
		else if (clazz.equals(Type.class)) value = AnyConverter.toType(object);
		else if (clazz.equals(Boolean.class)) value = new Boolean(AnyConverter.toBoolean(object));
		else if (clazz.equals(Character.class)) value = new Character(AnyConverter.toChar(object));
		else if (clazz.equals(Byte.class)) value = new Byte(AnyConverter.toByte(object));
		else if (clazz.equals(Short.class)) value = new Short(AnyConverter.toShort(object));
		else if (clazz.equals(Integer.class)) value = new Integer(AnyConverter.toInt(object));
		else if (clazz.equals(Long.class)) value = new Long(AnyConverter.toLong(object));
		else if (clazz.equals(Float.class)) value = new Float(AnyConverter.toFloat(object));
		else if (clazz.equals(Double.class)) value = new Double(AnyConverter.toDouble(object));
		else if (XInterface.class.isAssignableFrom(clazz)) value = AnyConverter.toObject(new Type(clazz), object);
		else if (com.sun.star.uno.Enum.class.isAssignableFrom(clazz)) value = AnyConverter.toObject(new Type(clazz), object);
		else throw new com.sun.star.lang.IllegalArgumentException("Could not convert the argument");
		return value;
	}

	public static void setPropertyValueNoBroadcast(Property property,
												   Object value,
												   Object object,
												   Object id)
	throws com.sun.star.lang.WrappedTargetException
	{
		Method method = null;
		String setter = "set" + id;
		try 
		{
			method = object.getClass().getMethod(setter, property.Type.getZClass());
		}
		catch (SecurityException | NoSuchMethodException e)
		{
			String msg = e.getMessage();
			e.printStackTrace();
			throw new WrappedTargetException(msg);
		}
		try
		{
			if (method != null)
			{
				method.invoke(object, value);
			}
		}
		catch (java.lang.IllegalArgumentException e)
		{
			String msg = e.getMessage();
			throw new IllegalArgumentException(msg);
		}
		catch (IllegalAccessException | InvocationTargetException e)
		{
			String msg = e.getMessage();
			throw new WrappedTargetException(msg);
		}
	}


	public static Object getPropertyValue(Property property,
										  Object object,
										  Object id)
	{
		Method method = null;
		String getter = "get" + id;
		try {
			method = object.getClass().getMethod(getter);
		}
		catch (NoSuchMethodException | SecurityException e)
		{
			e.printStackTrace();
		}
		Object value = null;
		try
		{
			value = method.invoke(object);
		}
		catch (IllegalAccessException | InvocationTargetException e)
		{
			e.printStackTrace();
		}
		return value;
	}


}
